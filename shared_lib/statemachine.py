# shared_lib/statemachine.py
#type: ignore
"""
Classes to treat the software-driven laboratory subsystems as state machines

Author(s): BoB LeSuer
"""
from .utility import check_if_microcontroller
from .message_buffer import LinearMessageBuffer
from shared_lib.messages import send_problem, send_success
from time import monotonic

if check_if_microcontroller():
    import adafruit_logging as logging
else:
    import logging

class StateMachine:
    """
    A class to represent a state machine.
    """

    def __init__(self, name: str, config: dict, version: str = "0.0.0", init_state: str = 'Initialize', status_callback=None, background_callback=None):
        """
        Constructs all the necessary attributes for the state machine object.
        """
        # Read only properties
        self._name = name
        self._version = version
        self._config = config
        self._init_state = init_state
        self._idle_state = 'Idle'

        # Mutable properties
        self.state = None
        self.states = {}
        self.flags = {} 
        self.command_handlers = {}
        self.supported_commands = {}
        self.running = False
        self.is_microcontroller = check_if_microcontroller()
        self.sequencer = StateSequencer(self)

        # Background task hook (Option A)
        self.background_callback = background_callback

        # Populate status info
        self.build_status_info = status_callback if status_callback is not None else lambda m: {}

        # Each state machine has an inbox
        self.inbox = LinearMessageBuffer()
        if not self.is_microcontroller:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)s] %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(self.name)

    # Read only properties
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def config(self) -> dict:
        return self._config
    
    @property
    def init_state(self) -> str:
        return self._init_state
    
    @property
    def idle_state(self) -> str:
        return self._idle_state

    def add_command(self, name: str, handler, doc: dict):
        self.command_handlers[name] = handler
        self.supported_commands[name] = doc
        
    def handle_instruction(self, payload: dict):
        func_name = payload.get("func") if isinstance(payload, dict) else None
        handler = self.command_handlers.get(func_name)
        if handler:
            handler(self, payload)
        else:
            self._handle_unknown(payload)
            
    def _handle_unknown(self, payload: dict):
        func_name = payload.get("func") if payload else "N/A"
        self.log.error(f"Received an unknown instruction: {func_name}")
        send_problem(self, {"message": f"{func_name} is unknown."})

    def add_state(self, state):
        if not getattr(state, "name", None):
            raise ValueError(f"State {state.__class__.__name__} must define a non-empty 'name'.")
        if state.name in self.states:
            raise ValueError(f"Duplicate state name: {state.name}")
        self.states[state.name] = state

    def add_flag(self, flag: str, init_value):
        self.flags[flag] = init_value

    def go_to_state(self, state_name: str, context=None):
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            self.state.exit(self)
        
        self.state = self.states.get(state_name)
        if not self.state:
            raise ValueError(f"Attempted to transition to an unknown state: '{state_name}'")
            
        try:
            self.state.enter(self, context=context)
        except ContextError as e:
            self.log.error(f"Aborting sequence. Reason: {e}.")
            if self.sequencer.is_active:
                self.sequencer.abort(e)

    def update(self):
        """
        Updates the current state of the state machine, running the background
        callback first if one has been registered.
        """
        if not self.running:
            raise Exception('State machine must be running to do this.')

        # Execute registered background callback before state execution
        # Avoids executing if in Error state to prevent trace loops on hard faults
        if self.background_callback and (not self.state or self.state.name != 'Error'):
            try:
                self.background_callback(self)
            except Exception as e:
                self.log.critical(f"Unhandled exception in background callback: {e}")
                self.flags['error_message'] = f"Background task failure: {e}"
                self.go_to_state('Error')

        if self.state:
            self.state.update(self)

    def run(self, state_name: str = None):
        self.running = True
        if state_name is None:
            self.go_to_state(self._init_state)
        else:
            self.go_to_state(state_name)

    def stop(self):
        self.running = False

class ContextError(Exception):
    pass

class State:
    def __init__(self):
        self.entered_at = 0
        self.required_context = []
        self.task_complete = False

    def _validate_context(self, machine: StateMachine, context: dict):
        if machine.sequencer.is_active:
            for key in self.required_context:
                if key not in machine.sequencer.context:
                    raise ContextError(f"State '{self.name}' requires '{key}'.")
 
    @property
    def name(self) -> str:
        return ''

    def enter(self, machine: StateMachine, context=None):
        self.entered_at = monotonic()
        self.local_context = context or {}
        self._validate_context(machine, self.local_context)
        self.task_complete = False
        machine.log.info(f'{machine.name} entered {self.name} with context={self.local_context}.')

    def exit(self, machine: StateMachine):
        machine.log.info(f'{machine.name} left {self.name} after {round(monotonic()-self.entered_at,3)} seconds.')

    def update(self, machine: StateMachine):
        if self.task_complete:
            machine.sequencer.advance()

class StateMachineOrchestrator:
    def __init__(self):
        self.state_machines = {}

    def add_state_machine(self, name: str, state_machine: StateMachine):
        self.state_machines[name] = state_machine

    def remove_state_machine(self, name: str):
        if name in self.state_machines:
            del self.state_machines[name]

    def update(self):
        for state_machine in self.state_machines.values():
            state_machine.update()

    def run_all(self):
        for state_machine in self.state_machines.values():
            state_machine.run()

    def stop_all(self):
        for state_machine in self.state_machines.values():
            state_machine.stop()    

class StateSequencer:
    def __init__(self, machine: StateMachine):
        self.machine = machine
        self.queue = []
        self.context = {}
        self._is_active = False
        self._persistent = False

    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def start(self, sequence_list: list, persistent: bool = False, initial_context: dict = None):
        if self._is_active:
            send_problem(self.machine, "Device is busy with another task.")
            return
        
        if not sequence_list:
            send_problem(self.machine, "Cannot start an empty sequence.")
            return
        
        self.machine.log.info(f"Starting sequence: {sequence_list} -> persistent ='{persistent}'")
        self._is_active = True
        self.queue = sequence_list[:]
        self._persistent = persistent
        self.context = initial_context if initial_context is not None else {}
        self.advance()
    
    def abort(self, reason: str):
        send_problem(self.machine, f"Sequence aborted: {reason}")
        self._reset()
        self.machine.go_to_state(self.machine.idle_state)

    def advance(self):
        if not self.is_active:
            self.machine.log.debug("advance() called outside of a sequence. Returning to idle state")
            self.machine.go_to_state(self.machine.idle_state)
            return

        if not self.queue:
            self._complete()
            return
        
        step = self.queue.pop(0)
        if not isinstance(step, dict) or "state" not in step:
            self.machine.log.error(f"Invalid step format: {step}")
            self.abort("Invalid sequence step format")
            return
        
        state_name = step["state"]
        self.current_label = step.get("label")
        step_context = step.get("context", {})
        label_info = f" ({self.current_label})" if self.current_label else ""
        
        self.machine.log.info(f"Advancing to {state_name}{label_info} with context = {step_context}")
        self.machine.go_to_state(state_name, context=step_context)
    
    def _complete(self):
        self.machine.log.info("Sequence complete.")
        sequence_name = self.context.get('name','Unnamed')
        send_success(self.machine, f"Sequence {sequence_name} completed successfully")
        
        was_persistent_sequence = self._persistent
        self._reset()

        if not was_persistent_sequence:
            self.machine.go_to_state(self.machine.idle_state)
    
    def _reset(self):
        self._is_active = False
        self.queue.clear()
        self.context.clear()
        self._persistent = False