#type: ignore
"""
Classes to treat the software-driven laboratory subsystems as state machines

Author(s): BoB LeSuer
"""
from .utility import check_if_microcontroller
from .message_buffer import MessageBuffer
from time import monotonic

if check_if_microcontroller():
    import adafruit_logging as logging
else:
    import logging

class StateMachine:
    """
    A class to represent a state machine.

    Attributes:
    -----------
    state : State
        The current state of the state machine.
    states : dict
        A dictionary of all states in the state machine.
    flags : dict
        A dictionary of flags used in the state machine.
    running : bool
        Indicates whether the state machine is running.
    is_microcontroller : bool
        Indicates whether the system is a microcontroller.
    init_state : str
        The initial state of the state machine.

    Methods:
    --------
    add_state(state):
        Adds a state to the state machine.
    add_flag(flag, init_value):
        Adds a flag to the state machine.
    go_to_state(state_name):
        Transitions the state machine to the specified state.
    update():
        Updates the current state of the state machine.
    run(state_name=None):
        Starts the state machine.
    stop():
        Stops the state machine.
    """

    def __init__(self, init_state='Initialize', name=None):
        """
        Constructs all the necessary attributes for the state machine object.

        Parameters:
        -----------
        init_state : str, optional
            The initial state of the state machine (default is 'Initialize').
        """
        self.state = None
        self.states = {}
        self.flags = {} # Includes parameters. May want to separate in the future
        self.running = False
        self.is_microcontroller = check_if_microcontroller()
        self.init_state = init_state
        self.name = name
        # Each state machine has a log 
        self.buffer = MessageBuffer()
        #self.handler = MessageBufferHandler(self.buffer, subsystem_name = self.name)
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(self.name)
        #self.log.setLevel(logging.INFO)
        #self.log.addHandler(self.handler)
        #self.log.addHandler(self.handler)
        
    def add_state(self, state):
        """
        Adds a state to the state machine.

        Parameters:
        -----------
        state : State
            The state to be added.
        """
        self.states[state.name] = state

    # Would eventually want the ability to add flags during state instantiation 
    def add_flag(self, flag, init_value):
        """
        Adds a flag to the state machine.

        Parameters:
        -----------
        flag : str
            The name of the flag.
        init_value : any
            The initial value of the flag.
        """
        self.flags[flag] = init_value

    def go_to_state(self, state_name):
        """
        Transitions the state machine to the specified state.

        Parameters:
        -----------
        state_name : str
            The name of the state to transition to.

        Raises:
        -------
        Exception:
            If the state machine is not running.
        """
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]
        self.state.enter(self)

    def update(self):
        """
        Updates the current state of the state machine.

        Raises:
        -------
        Exception:
            If the state machine is not running.
        """
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            self.state.update(self)

    def run(self, state_name=None):
        """
        Starts the state machine.

        Parameters:
        -----------
        state_name : str, optional
            The name of the state to start with (default is None).
        """
        self.running = True
        if state_name is None:
            self.go_to_state(self.init_state)
        else:
            self.go_to_state(state_name)

    def stop(self):
        """
        Stops the state machine.
        """
        self.running = False


class State:
    """
    A class to represent a state in the state machine.

    Attributes:
    -----------
    entered_at : float
        The time when the state was entered.

    Methods:
    --------
    name():
        Returns the name of the state.
    enter(machine):
        Actions to perform when entering the state.
    exit(machine):
        Actions to perform when exiting the state.
    update(machine):
        Actions to perform when updating the state.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the state object.
        """
        self.entered_at = 0
 
    @property
    def name(self):
        """
        Returns the name of the state.

        Returns:
        --------
        str:
            The name of the state.
        """
        return ''

    def enter(self, machine):
        """
        Actions to perform when entering the state.

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        self.entered_at = monotonic()

    def exit(self, machine):
        """
        Actions to perform when exiting the state. Override default behavior with custom exit function

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        machine.log.info(f'{machine.name} left {self.name} after {round(monotonic()-self.entered_at,3)} seconds.')

    def update(self, machine):
        """
        Actions to perform when updating the state.

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        pass

class StateMachineOrchestrator:
    """
    A class to manage and coordinate multiple state machines.
    
    Attributes:
    -----------
    state_machines : dict
        A dictionary of state machines managed by the orchestrator
    
    Methods:
    --------
    add_state_machine(name, state_machine):
        Adds a state machine to the orchestrator
    remove_state_machine(name):
        Removes a state machine from the orchestrator
    update():
        Updates all state machines managed by the orchestrator
    run_all():
        Starts all state machines managed by the orchestrator
    stop_all():
        Stops all state machines managed by the orchestrator
    """
    def __init__(self):
        """
        Constructs all the necessary attributes for the state machine orchestrator object.
        """
        self.state_machines = {}

    def add_state_machine(self, name, state_machine):
        """
        Adds a state machine to the orchestrator.

        Parameters:
        -----------
        name : str
            The name of the state machine.
        state_machine : StateMachine
            The state machine to be added.
        """
        self.state_machines[name] = state_machine

    def remove_state_machine(self, name):
        """
        Removes a state machine from the orchestrator.

        Parameters:
        -----------
        name : str
            The name of the state machine to be removed.
        """
        if name in self.state_machines:
            del self.state_machines[name]

    def update(self):
        """
        Updates all state machines managed by the orchestrator.
        """
        for state_machine in self.state_machines.values():
            state_machine.update()

    def run_all(self):
        """
        Starts all state machines managed by the orchestrator.
        """
        for state_machine in self.state_machines.values():
            state_machine.run()

    def stop_all(self):
        """
        Stops all state machines managed by the orchestrator.
        """
        for state_machine in self.state_machines.values():
            state_machine.stop()    