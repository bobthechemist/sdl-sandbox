## Directory: `./shared_lib`

### `__init__.py`

```python
"""
This module serves as the entry point for the shared library. It is responsible for initializing and managing various components that are shared across different modules.
"""

# Import necessary modules and classes from other files within the shared_lib package
from .message_buffer import MessageBuffer, LinearMessageBuffer, CircularMessageBuffer
from .messages import Message, send_problem, send_success
from .statemachine import StateMachine, ContextError, State, StateMachineOrchestrator, StateSequencer
from .utility import check_if_microcontroller

# Add any additional imports or initializations here if needed

```

### `error_handling.py`

```python
# shared_lib/error_handling.py
# Some helper functions for consistent error handling 
from shared_lib.messages import send_problem

def try_wrapper(func):
    """
    A decorator for wrapping try/except around logic.
    
    Args:
        func (Callable): The function to wrap with try/except.
        
    Returns:
        Callable: The wrapped function that includes error handling.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            machine = args[0] if args else kwargs.get('machine')
            extra = getattr(func, "err_msg", "nothing new")
            send_problem(machine, f"The function {func.__name__} raised an error: {e}.")
    return wrapper

def try_wrapper_broken(func):
    """
    A decorator for wrapping try/except around device command handlers.
    This version is compatible with CircuitPython (no functools).
    
    Args:
        func (Callable): The function to wrap with try/except.
        
    Returns:
        Callable: The wrapped function that includes error handling.
    """
    def wrapper(*args, **kwargs):
        try:
            # Execute the original function
            return func(*args, **kwargs)
        except Exception as e:
            # Gracefully handle any exceptions
            machine = args[0] if args else kwargs.get('machine')
            if machine:
                # Use the manually saved function name for the error report
                send_problem(machine, f"The function '{wrapper._name_}' raised an error: {e}")

    # --- The Fix for CircuitPython ---
    # Manually copy the name from the original function to the wrapper
    wrapper._name_ = func.__name__
    return wrapper

```

### `message_buffer.py`

```python
#type: ignore

# Base (abstract-ish) class for a buffer that will handle messages.
class MessageBuffer():
    """
    Base class for message buffer implementations.

    Args:
        max_size (int, optional): The maximum capacity of the buffer. Defaults to 100.
    """

    def __init__(self, max_size: int = 100):
        """
        Initializes the message buffer.

        Args:
            max_size (int, optional): The maximum capacity of the buffer. Defaults to 100.
        """
        self.messages = self._create_storage()  # Abstract method to create storage
        self.max_size = max_size  # Maximum capacity of the buffer (fixed)
        self.current_size = 0  # Track how many messages are in the buffer. Important for Circular Buffer
        # This is for the circular buffer, but it won't hurt the others.
        self.head = 0
        self.tail = 0

    def is_empty(self) -> bool:
        """
        Returns True if the buffer is empty, False otherwise.

        Returns:
            bool: True if the buffer is empty, False otherwise.
        """
        return self.current_size == 0

    def is_full(self) -> bool:
        """
        Returns True if the buffer is full, False otherwise.

        Returns:
            bool: True if the buffer is full, False otherwise.
        """
        return self.current_size >= self.max_size

    def store(self, value):
        """
        Stores a value in the message buffer.

        Args:
            value: The value to be stored in the buffer.

        Raises:
            OverflowError: If the buffer is full and cannot accommodate more messages.
        """
        if self.is_full():
            self._handle_full_buffer(value)  # handle the exception if the buffer is full
            return
        self._store(value)  # Implementation specific storing
        self.current_size += 1

    def get(self):
        """
        Retrieves the next message from the buffer (implementation-specific).

        Returns:
            The next message from the buffer, or None if the buffer is empty.
        """
        if self.is_empty():
            return None  # Or raise an exception if appropriate

        value = self._get()  # Implementation specific retrieval
        self.current_size -= 1
        return value

    def flush(self):
        """
        Empties the buffer.
        """
        self._flush()  # Implementation specific flushing
        self.current_size = 0
        self.head = 0
        self.tail = 0

    def _create_storage(self):
        """Creates a new storage object"""
        return []  # implementation specific

    def _handle_full_buffer(self, value):
        """Handles when the message buffer is full."""
        raise OverflowError("Buffer is full")

    def _store(self, value):
        """Stores a value in the buffer, Implementation Specific."""
        raise NotImplementedError("Implementation specific storing not implemented")

    def _get(self):
        """Retrieves a value from the buffer, Implementation Specific."""
        raise NotImplementedError("Implementation specific retrieval not implemented")

    def _flush(self):
        """Flushes the buffer, implementation specific."""
        raise NotImplementedError("Implementation specific flush not implemented")


class LinearMessageBuffer(MessageBuffer):
    """
    A simple linear FIFO message buffer implemented using a list.

    Args:
        max_size (int, optional): The maximum capacity of the buffer. Defaults to 100.
    """

    def __init__(self, max_size: int = 100):
        super().__init__(max_size)

    def _create_storage(self):
        return []

    def _store(self, value):
        """
        Stores a value in the linear message buffer.

        Args:
            value: The value to be stored.
        """
        self.messages.append(value)

    def _get(self):
        """
        Retrieves and removes the next message from the linear message buffer.

        Returns:
            The next message from the buffer, or None if the buffer is empty.
        """
        return self.messages.pop(0)

    def _flush(self):
        """
        Empties the linear message buffer.
        """
        self.messages = []


class CircularMessageBuffer(MessageBuffer):
    """
    A circular FIFO message buffer implemented using a list.

    Args:
        max_size (int, optional): The maximum capacity of the buffer. Defaults to 100.
    """

    def __init__(self, max_size: int = 100):
        super().__init__(max_size)

    def _create_storage(self):
        """
        Creates a new storage object for the circular message buffer.

        Returns:
            list: A list initialized with None values of size `max_size`.
        """
        return [None] * self.max_size  # initialize with None

    def _handle_full_buffer(self, value):
        """
        Handles when the circular message buffer is full by removing the oldest message.

        Args:
            value: The new value to be stored.
        """
        self._get()  # this handles the exception that happens on this circular buffer

    def _store(self, value):
        """
        Stores a value in the circular message buffer.

        Args:
            value: The value to be stored.
        """
        self.messages[self.tail] = value
        self.tail = (self.tail + 1) % self.max_size

        if self.is_full():
            self.head = (self.head + 1) % self.max_size  # If full, also advance the head

    def _get(self):
        """
        Retrieves and removes the next message from the circular message buffer.

        Returns:
            The next message from the buffer, or None if the buffer is empty.
        """
        if self.is_empty():
            return None  # Or raise an exception if appropriate

        value = self.messages[self.head]
        self.messages[self.head] = None  # clean the previous data
        self.head = (self.head + 1) % self.max_size
        return value

    def _flush(self):
        """
        Empties the circular message buffer.
        """
        self.messages = [None] * self.max_size
        self.head = 0
        self.tail = 0

```

### `messages.py`

```python
#type: ignore
import json
import time

class Message():
    """
    Represents a message with subsystem name, status, metadata, and payload.
    
    Args:
        subsystem_name (str, optional): The name of the subsystem that generated the message. Defaults to None.
        status (str, optional): The status level of the message. Must be one of VALID_STATUS. Defaults to None.
        meta (dict, optional): Additional metadata for the message. Defaults to an empty dictionary.
        payload (dict, optional): The main content of the message. Defaults to an empty dictionary.
        timestamp (float, optional): The timestamp when the message was created. Defaults to the current time.
        
    Raises:
        ValueError: If the status is not in VALID_STATUS or if JSON decoding fails.
        TypeError: If meta or payload is not a dictionary.
    """

    VALID_STATUS = {"DEBUG", "TELEMETRY", "INFO", "INSTRUCTION", "SUCCESS", "PROBLEM", "WARNING", "DATA_RESPONSE"}

    def __init__(self, subsystem_name=None, status=None, meta=None, payload=None, timestamp=None):
        """Initializes a Message object."""
        self._subsystem_name = subsystem_name
        # Validate that the status provided to the method is valid
        if status is not None and status not in Message.VALID_STATUS:
           raise ValueError("Invalid Status Level")
        self._status = status
        if meta is None:
            self._meta = {}
        elif not isinstance(meta, dict):
            raise TypeError("meta must be a dictionary")
        else:
            self._meta = meta
        if timestamp is None:
            self._timestamp = time.time()
        else:
            self._timestamp = timestamp
        if payload is None:
            self._payload = {}
        elif not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        else:
            self._payload = payload

    def to_dict(self):
        """Returns a dictionary representation of the message.
        
        Returns:
            dict: A dictionary containing the subsystem_name, status, meta, payload, and timestamp.
        """
        return {
            "subsystem_name": self.subsystem_name,
            "status": self.status,
            "meta": self.meta,
            "payload": self.payload,
            "timestamp": self.timestamp
        }

    def serialize(self):
        """Serializes the message to JSON.
        
        Returns:
            str: A JSON string representation of the message.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_string: str):
        """
        Creates a new Message instance from a JSON string.
        This is a class method.
        
        Args:
            json_string (str): The JSON string to deserialize.
            
        Returns:
            Message: A new Message instance created from the JSON string.
            
        Raises:
            ValueError: If the JSON string is invalid.
        """
        try:
            data = json.loads(json_string)
            subsystem_name = data.get("subsystem_name")
            status = data.get("status")
            meta = data.get("meta", {})
            payload = data.get("payload")
            timestamp = data.get("timestamp")
            # The validation for status is handled by the __init__ method,
            # so we just pass the values along.
            return cls(
                subsystem_name=subsystem_name,
                status=status,
                meta=meta,
                payload=payload,
                timestamp=timestamp
            )
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")

    @property
    def subsystem_name(self):
        """Getter for the subsystem_name property.
        
        Returns:
            str: The name of the subsystem that generated the message.
        """
        return self._subsystem_name

    @subsystem_name.setter
    def subsystem_name(self, value):
        """Setter for the subsystem_name property.
        
        Args:
            value (str): The new subsystem name to set.
        """
        self._subsystem_name = value

    @property
    def status(self):
        """Getter for the status property.
        
        Returns:
            str: The status level of the message.
        """
        return self._status
    
    @status.setter
    def status(self, value):
        """Setter for the status property.
        
        Args:
            value (str): The new status to set.
            
        Raises:
            ValueError: If the provided status is not in VALID_STATUS.
        """
        if value not in Message.VALID_STATUS:
            raise ValueError("Invalid Status Level")
        self._status = value

    @property
    def meta(self):
        """Getter for the meta property.
        
        Returns:
            dict: The metadata of the message. Currently returns a fake dictionary.
        """
        # we are ignoring any meta in envelope until this is implemented
        # Should append self._meta to the dict below.
        fake_meta = {
            "id": "fake UUID",
            "seq": -1,
            "origin": "fake UUID"
        }
        return fake_meta

    @meta.setter
    def meta(self, value):
        """Setter for the meta property.
        
        Args:
            value (dict): The new metadata to set.
            
        Raises:
            TypeError: If the provided value is not a dictionary.
        """
        if not isinstance(value, dict):
            raise TypeError("meta must be a dictionary")
        self._meta = value

    @property
    def payload(self):
        """Getter for the payload property.
        
        Returns:
            dict: The main content of the message.
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        """Setter for the payload property.
        
        Args:
            value (dict): The new payload to set.
            
        Raises:
            TypeError: If the provided value is not a dictionary.
        """
        if not isinstance(value, dict):
            raise TypeError("payload must be a dictionary")
        self._payload = value

    @property
    def timestamp(self):
        """Getter for the timestamp property.
        
        Returns:
            float: The timestamp when the message was created.
        """
        return self._timestamp

    @classmethod
    def create_message(cls, subsystem_name=None, status=None, meta=None, payload=None):
        """Creates a Message instance.
        
        Args:
            subsystem_name (str, optional): The name of the subsystem that generated the message. Defaults to None.
            status (str, optional): The status level of the message. Must be one of VALID_STATUS. Defaults to None.
            meta (dict, optional): Additional metadata for the message. Defaults to an empty dictionary.
            payload (dict, optional): The main content of the message. Defaults to an empty dictionary.
            
        Returns:
            Message: A new Message instance created with the provided arguments.
        """
        return cls(subsystem_name=subsystem_name, status=status, meta=meta, payload=payload)

    @classmethod
    def get_valid_status(cls):
        """Returns a set of valid status levels for messages.
        
        Returns:
            set: A set containing all valid status levels.
        """
        return cls.VALID_STATUS

# Make it easy to send properly formatted messages (at least for problem and success at the moment)

def send_problem(machine, msg, error = None):
    """A helper function to create and send a standardized PROBLEM message.
    
    Args:
        machine: The machine object that will log the error and send the message.
        msg (str): The main message describing the problem.
        error (Exception, optional): An exception object associated with the problem. Defaults to None.
        
    Raises:
        AttributeError: If the machine does not have a 'log' or 'postman' attribute.
    """
    machine.log.error(f"msg:{msg}, error:{error}")
    payload = {"message":msg}
    if error is not None:
        payload["exception"] = str(error)
    response = Message.create_message(
        subsystem_name=machine.name,
        status="PROBLEM",
        payload=payload
    )
    machine.postman.send(response.serialize())

def send_success(machine, msg):
    """A helper function to create and send a standardize SUCCESS message.
    
    Args:
        machine: The machine object that will log the success message and send it.
        msg (str): The main message describing the success.
        
    Raises:
        AttributeError: If the machine does not have a 'log' or 'postman' attribute.
    """
    machine.log.info(msg)
    response = Message(
        subsystem_name=machine.name,
        status="SUCCESS",
        payload={"message": msg}
    )
    machine.postman.send(response.serialize())

```

### `statemachine.py`

```python
# shared_lib/statemachine.py
#type: ignore
"""
Classes to treat the software-driven laboratory subsystems as state machines

Author(s): BoB LeSuer
"""
from .utility import check_if_microcontroller
from .message_buffer import LinearMessageBuffer # Keep it simple, although at some point, SM should be able to choose
from shared_lib.messages import send_problem, send_success
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

    def __init__(self, name: str, config: dict, version: str = "0.0.0", init_state: str = 'Initialize', status_callback=None):
        """
        Constructs all the necessary attributes for the state machine object.

        Parameters:
        -----------
        name : str
            The name of the state machine.
        config : dict
            Configuration settings for the state machine.
        version : str, optional
            The version of the state machine (default is '0.0.0').
        init_state : str, optional
            The initial state of the state machine (default is 'Initialize').
        status_callback : callable, optional
            A callback function to build status information (default is None).
        """

        # Read only properties
        self._name = name
        self._version = version
        self._config = config
        self._init_state = init_state
        self._idle_state = 'Idle' # TODO: Replace hardcoded Idle statements with this and allow for modification

        # Mutable properties
        self.state = None
        self.states = {}
        self.flags = {} 
        self.command_handlers = {}
        self.supported_commands = {}
        self.running = False
        self.is_microcontroller = check_if_microcontroller()
        self.sequencer = StateSequencer(self)

        # Populate status info
        self.build_status_info = status_callback if status_callback is not None else lambda m: {}

        # Each state machine has an inbox
        self.inbox = LinearMessageBuffer()
        # TODO: Create a custom handler or other solution to address that adafruit_logging doesn't have basicConfig
        if not self.is_microcontroller:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)s] %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(self.name)

    # Read only properites
    @property
    def name(self) -> str:
        """
        Returns the name of the state machine.

        Returns:
        --------
        str
            The name of the state machine.
        """
        return self._name
    
    @property
    def version(self) -> str:
        """
        Returns the version of the state machine.

        Returns:
        --------
        str
            The version of the state machine.
        """
        return self._version
    
    @property
    def config(self) -> dict:
        """
        Returns the configuration settings of the state machine.

        Returns:
        --------
        dict
            Configuration settings of the state machine.
        """
        return self._config
    
    @property
    def init_state(self) -> str:
        """
        Returns the initial state of the state machine.

        Returns:
        --------
        str
            The initial state of the state machine.
        """
        return self._init_state
    
    @property
    def idle_state(self) -> str:
        """
        Returns the idle state of the state machine.

        Returns:
        --------
        str
            The idle state of the state machine.
        """
        return self._idle_state

    def add_command(self, name: str, handler, doc: dict):
        """Adds a command handler and its documentation to the machine."""
        self.command_handlers[name] = handler
        self.supported_commands[name] = doc
        
    def handle_instruction(self, payload: dict):
        """
        Dispatches an instruction payload to the correct handler.

        Parameters:
        -----------
        payload : dict
            The instruction payload to be handled.
        """
        # Handler should set any flags and move to a different state
        
        func_name = payload.get("func") if isinstance(payload, dict) else None
        
        handler = self.command_handlers.get(func_name)
        
        if handler:
            # Call the handler, passing the machine instance and payload
            handler(self, payload)
        else:
            self._handle_unknown(payload)
            
    def _handle_unknown(self, payload: dict):
        """
        Default handler for any command not found.

        Parameters:
        -----------
        payload : dict
            The unknown instruction payload.
        """
        func_name = payload.get("func") if payload else "N/A"
        self.log.error(f"Received an unknown instruction: {func_name}")
        send_problem(self, {"message": f"{func_name} is unknown."})

    def add_state(self, state):
        """
        Adds a state to the state machine.

        Parameters:
        -----------
        state : State
            The state to be added.
        
        Raises:
        -------
        ValueError:
            If the state does not define a non-empty 'name' or if there is a duplicate state name.
        """
        if not getattr(state, "name", None):
            raise ValueError(f"State {state.__class__.__name__} must define a non-empty 'name'.")
        if state.name in self.states:
            raise ValueError(f"Duplicate state name: {state.name}")
        self.states[state.name] = state

    def add_flag(self, flag: str, init_value):
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

    def go_to_state(self, state_name: str, context=None):
        """
        Transitions the state machine to the specified state.

        Parameters:
        -----------
        state_name : str
            The name of the state to transition to.
        context : dict, optional
            Context data for the new state (default is None).
        
        Raises:
        -------
        Exception:
            If the state machine is not running or if the specified state does not exist.
        """
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

    def run(self, state_name: str = None):
        """
        Starts the state machine.

        Parameters:
        -----------
        state_name : str, optional
            The name of the state to start with (default is None).
        """
        self.running = True
        if state_name is None:
            self.go_to_state(self._init_state)
        else:
            self.go_to_state(state_name)

    def stop(self):
        """
        Stops the state machine.
        """
        self.running = False

class ContextError(Exception):
    """Error for sequencer"""
    pass

class State:
    """
    A class to represent a state in the state machine.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the state object.
        """
        self.entered_at = 0
        self.required_context = []
        self.task_complete = False

    def _validate_context(self, machine: StateMachine, context: dict):
        """
        A private helper called by enter() to ensure the state has what it needs.

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        context : dict
            Context data for the state.
        
        Raises:
        -------
        ContextError:
            If a required context key is missing.
        """
        if machine.sequencer.is_active:
            for key in self.required_context:
                if key not in machine.sequencer.context:
                    raise ContextError(f"State '{self.name}' requires '{key}'.")
 
    @property
    def name(self) -> str:
        """
        Returns the name of the state.

        Returns:
        --------
        str
            The name of the state.
        """
        return ''

    # <<< FIX IS HERE: Signature updated.
    def enter(self, machine: StateMachine, context=None):
        """
        Actions to perform when entering the state.

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        context : dict, optional
            Context data for the new state (default is None).
        """
        self.entered_at = monotonic()
        self.local_context = context or {}
        self._validate_context(machine, self.local_context)
        self.task_complete = False
        machine.log.info(f'{machine.name} entered {self.name} with context={self.local_context}.')

    def exit(self, machine: StateMachine):
        """
        Actions to perform when exiting the state. Override default behavior with custom exit function

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        machine.log.info(f'{machine.name} left {self.name} after {round(monotonic()-self.entered_at,3)} seconds.')

    def update(self, machine: StateMachine):
        """
        Handles advancement logic. Should be called at the end of a state's update function

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        if self.task_complete:
            # Let the sequencer know this state's task is done.
            machine.sequencer.advance()

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

    def add_state_machine(self, name: str, state_machine: StateMachine):
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

    def remove_state_machine(self, name: str):
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

class StateSequencer:
    """
    Manages INSTRUCTION-initiated workflows for a StateMachine
    """
    def __init__(self, machine: StateMachine):
        self.machine = machine
        self.queue = []
        self.context = {}
        self._is_active = False
        self._persistent = False # Default to transient behavior

    @property
    def is_active(self) -> bool:
        """
        Returns whether the sequencer is active.

        Returns:
        --------
        bool
            True if the sequencer is active, False otherwise.
        """
        return self._is_active
    
    def start(self, sequence_list: list, persistent: bool = False, initial_context: dict = None):
        """
        Initiates a workflow

        Parameters:
        -----------
        sequence_list : list
            A list of steps in the sequence.
        persistent : bool, optional
            Whether the sequence should be persistent (default is False).
        initial_context : dict, optional
            Initial context for the sequence (default is None).
        
        Raises:
        -------
        Exception:
            If the sequencer is already active or if the sequence list is empty.
        """
        if self._is_active:
            send_problem(self.machine, "Device is busy with another task.")
            return
        
        if not sequence_list:
            send_problem(self.machine, "Cannot start an empty sequence.")
            return
        
        self.machine.log.info(f"Starting sequence: {sequence_list} -> persistent ='{persistent}'")
        self._is_active = True
        self.queue = sequence_list[:] # Make a copy
        self._persistent = persistent
        self.context = initial_context if initial_context is not None else {}
        self.advance()
    
    def abort(self, reason: str):
        """ Gracefully abort an active sequence. """
        send_problem(self.machine, f"Sequence aborted: {reason}")
        self._reset()
        self.machine.go_to_state(self.machine.idle_state)

    def advance(self):
        """
        Signal that the current state has completed its task.
        Internal method to run the next step or complete the sequence.
        """
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
        """
        Handles the completion of a sequence
        """
        self.machine.log.info("Sequence complete.")
        sequence_name = self.context.get('name','Unnamed')
        send_success(self.machine, f"Sequence {sequence_name} completed successfully")
        
        was_persistent_sequence = self._persistent
        self._reset()

        if not was_persistent_sequence:
            self.machine.go_to_state(self.machine.idle_state)
    
    def _reset(self):
        """Resets the sequencer to a clean state."""
        self._is_active = False
        self.queue.clear()
        self.context.clear()
        self._persistent = False

```

### `utility.py`

```python
import sys

def check_if_microcontroller() -> bool:
    """
    Determine if the code is running on a microcontroller using CircuitPython.

    Returns:
        bool: True if the code is running on CircuitPython, False otherwise.
    """
    try:
        if sys.implementation.name == 'circuitpython':
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

```

## Directory: `./firmware/sidekick`

### `__init__.py`

```python
# firmware/sidekick/__init__.py
# type: ignore
import board
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from our common firmware library
from firmware.common.common_states import GenericErrorWithButton, GenericIdle
from firmware.common.command_library import register_common_commands

# Import the device-specific parts we will write
from . import states
from . import handlers
from . import kinematics

# ============================================================================
# 1. INSTRUMENT CONFIGURATION
# ============================================================================
SUBSYSTEM_NAME = "SIDEKICK"
SUBSYSTEM_VERSION = "1.1.0" 
SUBSYSTEM_INIT_STATE = "Initialize"
SUBSYSTEM_CONFIG = {
    "pins": {
        # M1 is the top motor, controls A1 (arm with arrow)
        "motor1_step": board.GP1, "motor1_dir": board.GP0, "motor1_enable": board.GP7,
        "motor2_step": board.GP10, "motor2_dir": board.GP9, "motor2_enable": board.GP16,
        "motor1_m0": board.GP6, "motor1_m1": board.GP5,
        "motor2_m0": board.GP15, "motor2_m1": board.GP14,
        "endstop_m1": board.GP18, "endstop_m2": board.GP19,
        "user_button": board.GP20,
        "pump1": board.GP27, "pump2": board.GP26, "pump3": board.GP22, "pump4": board.GP21,
    },
    "motor_settings": {
        "step_angle_degrees": 0.9, "microsteps": 8, "max_speed_sps": 200,
    },
    "pump_timings": {
        "aspirate_time": 0.25, "dispense_time": 0.25, "increment_ul": 10.0,
    },
    "kinematics": {
        "L1": 7.0, "L2": 3.0, "L3": 10, "Ln": 0.5,
    },
    "safe_limits": {
        # These are placeholder values and need to be updated.
        "m1_max_steps": 1600, "m2_max_steps": 1600,
    },
    "homing_settings": {
        # The number of steps for M1 to back off endstop 2.
        "joint_backoff_steps": 20,
        # Set the position of the arm after homing
        "park_move_x": 10.0, # cm
        "park_move_y": 7.0, # cm
    },
        "operational_limits_degrees": {
        "m1_min": 0.0,
        "m1_max": 160.0,
        "m2_min": 80.0,
        "m2_max": 180.0
    },
    "plate_geometry": {
        "well_pitch_cm": 0.9,
        "rows": "ABCDEFGH",
        "columns": 12
    },
    "A1_offset": {
        "dx": 7.59, #7.24, 
        "dy": -5.3, #-5.57
    },
    "step_correction":{
        "m1e": -4,
        "m2e": 29,
    },
    # End effector orientation may not be the same as sidekick
    "pump_offsets": {
        "p1": {"dx": 1.09, "dy": -0.6}, "p2": {"dx": 1.09, "dy": -0.2},
        "p3": {"dx": 1.09, "dy": 0.2}, "p4": {"dx": 1.09, "dy": 0.6},
    },
    "ai_guidance": (
        "1. This device MUST be homed using the 'home' command at the start of every session "
        "before any other movement commands will work.\n"
        "2. To position a specific PUMP over a well for dispensing, use to_well(well='A1', pump='p1').\n"
        "3. To position the COLORIMETER over a well for measurement, use to_well(well='A1') "
        "and OMIT the 'pump' argument entirely. This centers the arm center-point."
    ),
}

# ============================================================================
# 2. ASSEMBLY SECTION
# ============================================================================

# This callback defines the device's specific telemetry data.
def send_telemetry(machine):
    """Generates and sends telemetry message."""
    m1_steps = machine.flags.get('current_m1_steps', 0)
    m2_steps = machine.flags.get('current_m2_steps', 0)
    theta1, theta2 = kinematics.steps_to_degrees(machine, m1_steps, m2_steps)
    x_pos, y_pos = kinematics.forward_kinematics(machine, theta1, theta2)

    telemetry_message = Message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={
            "data": {
                "x(world)": x_pos,
                "y(world)": y_pos
            }
        }
    )
    machine.postman.send(telemetry_message.serialize())

def build_status(machine):
    """
    This function is called by the generic get_info command.
    It builds a comprehensive, instrument-specific status dictionary in real-time.
    """
    # 1. Get the primary data: current motor steps
    m1_steps = machine.flags.get('current_m1_steps', 0)
    m2_steps = machine.flags.get('current_m2_steps', 0)

    # 2. Use kinematics to calculate derived values
    # These calculations are performed on the device at the moment of the request.
    theta1, theta2 = kinematics.steps_to_degrees(machine, m1_steps, m2_steps)
    x_pos, y_pos = kinematics.forward_kinematics(machine, theta1, theta2)
    
    # 3. Return the complete, detailed status dictionary
    return {
        "is_homed": machine.flags.get('is_homed', False),
        "raw_motor_steps": {
            "m1": m1_steps,
            "m2": m2_steps
        },
        "calculated_motor_angles_deg": {
            "theta1": round(theta1, 2),
            "theta2": round(theta2, 2)
        },
        "device_calculated_cartesian_cm": {
            "x": round(x_pos, 4),
            "y": round(y_pos, 4)
        }
    }

# --- Machine Assembly ---
machine = StateMachine(
    name=SUBSYSTEM_NAME,
    version=SUBSYSTEM_VERSION,
    config=SUBSYSTEM_CONFIG,
    init_state=SUBSYSTEM_INIT_STATE,
    status_callback=build_status
)

# --- Attach Communication Channel ---
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# --- Add States ---
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_telemetry))
machine.add_state(states.Homing())
machine.add_state(states.Moving())
machine.add_state(states.Dispensing())
machine.add_state(GenericErrorWithButton(reset_pin=machine.config['pins']['user_button'], reset_state_name='Idle'))

# --- Define Command Interface ---
# The common commands are registered here, but their `ai_enabled` flag is set to False by default.
# Only specific high-level commands will be exposed to the AI planner.
register_common_commands(machine) 
machine.add_command("home", handlers.handle_home, {
    "description": "Finds motor zero via endstops, then moves to a safe parking spot.",
    "args": [],
    "ai_enabled": True,
    "effects": ["arm is now in a known, safe park position", "is_homed flag is now true"]
})
machine.add_command("move_to", handlers.handle_move_to, {
    "description": "Moves the arm's center point to an absolute (x, y) coordinate.",
    "args": [
        {"name": "x", "type": "float", "description": "Target x-coordinate (cm)"},
        {"name": "y", "type": "float", "description": "Target y-coordinate (cm)"},
        {"name": "pump", "type": "str|int", "description": "Optional: pump nozzle to position over the well (e.g., 'p2' or 2). Defaults to end effector center.", "default": 0}
    ],
    "ai_enabled": True
})
machine.add_command("move_rel", handlers.handle_move_rel, {
    "description": "Moves the arm relative to its current position by (dx, dy).",
    "args": [
        {"name": "dx", "type": "float", "description": "Relative move in x-axis (cm)"},
        {"name": "dy", "type": "float", "description": "Relative move in y-axis (cm)"}
    ],
    "ai_enabled": True
})
machine.add_command("dispense", handlers.handle_dispense, {
    "description": "Dispenses from a pump at the current location.",
    "args": [
        {"name": "pump", "type": "str", "description": "Pump to use (e.g., 'p1')", "default": 0},
        {"name": "vol", "type": "float", "description": "Volume to dispense (uL)", "default": 10.0}
    ],
    "ai_enabled": True,
    "effects": ["liquid is added to the current well", "arm position does NOT change"],
    "usage_notes": "This command MUST be immediately preceded by a 'to_well' command that targets the correct pump nozzle."
})
machine.add_command("dispense_at", handlers.handle_dispense_at, {
    "description": "Moves a pump to an absolute (x, y) coordinate and then dispenses.",
    "args": [
        {"name": "pump", "type": "str", "description": "Pump to use (e.g., 'p1')"},
        {"name": "vol", "type": "float", "description": "Volume to dispense (uL)", "default": 10.0},
        {"name": "x", "type": "float", "description": "Target x-coordinate (cm)"},
        {"name": "y", "type": "float", "description": "Target y-coordinate (cm)"}
    ],
    "ai_enabled": True
})
machine.add_command("steps", handlers.handle_steps, {
    "description": "Moves motors by a relative number of steps. FOR TESTING ONLY.",
    "args": [
        {"name": "m1", "type": "int", "description": "Relative steps for motor 1"},
        {"name": "m2", "type": "int", "description": "Relative steps for motor 2"}
    ],
    "ai_enabled": False
})
machine.add_command("to_well", handlers.handle_to_well, {
    "description": "Moves to a specified well on a 96-well plate",
    "args": [
        {"name": "well", "type": "str", "description": "Target well designation (e.g., 'B6', 'h12')."},
        {"name": "pump", "type": "str|int", "description": "Optional: pump nozzle to position over the well (e.g., 'p2' or 2). Defaults to end effector center.", "default": 0}
    ],
    "ai_enabled": True,
    "effects": ["arm moves to center the target (pump or colorimeter) over the specified well"],
    "usage_notes": "To prepare for a 'dispense' action, you MUST use the 'pump' argument in this command. To prepare for a 'measure' action, the 'pump' argument should be omitted to center the arm."
})

# Override common commands to ensure they are not used by the AI
machine.supported_commands['help']['ai_enabled'] = False
machine.supported_commands['ping']['ai_enabled'] = False
machine.supported_commands['set_time']['ai_enabled'] = False
machine.supported_commands['get_info']['ai_enabled'] = False

# --- Add Dynamic Flags
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 60.0)
# --- Public flags are available via get_info ---
machine.add_flag('is_homed', False)
# --- Positioning flags ---
machine.add_flag('current_m1_steps', 0)
machine.add_flag('current_m2_steps', 0)
machine.add_flag('target_m1_steps', 0)
machine.add_flag('target_m2_steps', 0)
# --- Dispensing flags ---
machine.add_flag('dispense_pump', None)
machine.add_flag('dispense_cycles', 0)
machine.add_flag('on_move_complete', None) # For the state sequencer
```

### `handlers.py`

```python
# firmware/sidekick/handlers.py
# type: ignore
from shared_lib.messages import Message, send_problem, send_success
from . import kinematics
import math
from shared_lib.error_handling import try_wrapper
import re


def get_current_position_steps(machine):
    """Returns the current position as a tuple of motor steps: (m1, m2)."""
    return (
        machine.flags.get('current_m1_steps', 0),
        machine.flags.get('current_m2_steps', 0)
    )

def get_current_position_degrees(machine):
    """
    Converts current motor steps to degrees.
    Returns: (theta1, theta2)
    """
    m1_steps, m2_steps = _get_current_position_steps(machine)
    return kinematics.steps_to_degrees(machine, m1_steps, m2_steps)

def get_current_position_cartesian(machine):
    """
    Calculates the current Cartesian position of the arm.
    Returns: (x, y)
    """
    theta1, theta2 = _get_current_position_degrees(machine)
    return kinematics.forward_kinematics(machine, theta1, theta2)

def check_homed(machine):
    """Guard condition to ensure the device is homed."""
    if not machine.flags.get('is_homed', False):
        send_problem(machine, "Device must be homed before this operation.")
        return False
    return True

def degrees_to_steps(machine, theta1, theta2):
    """Converts motor angles in degrees to absolute step counts."""
    cfg = machine.config['motor_settings']
    steps_per_rev = (360 / cfg['step_angle_degrees']) * cfg['microsteps']
    
    m1_steps = int((theta1 / 360) * steps_per_rev)
    m2_steps = int((theta2 / 360) * steps_per_rev)
    
    return m1_steps, m2_steps

def parse_well_designation(machine, well_str: str):
    """
    Parses a well string (e.g., 'B6') into zero-based (row, column) indices.
    Returns a tuple or None if invalid.
    """
    if not isinstance(well_str, str): return None
    
    plate_geo = machine.config['plate_geometry']
    rows = plate_geo['rows']
    
    sanitized_well = well_str.upper().strip()
    # Build a regex dynamically from the config
    match = re.match(r'^([' + rows + '])([1-9]|1[0-2])$', sanitized_well)
    
    if not match: return None

    letter_part = match.group(1)
    number_part = int(match.group(2))
    
    row_index = rows.find(letter_part)
    col_index = number_part - 1
    
    return (row_index, col_index)

def calculate_dispense_cycles(machine, volume, pump):
    """
    Calculates the number of cycles to perform to dispense liquid
    TODO: Consider implementing a calibrated volume instead of assuming 10 uL
    """
    increment = machine.config['pump_timings']['increment_ul']
    cycles = int(volume//increment)
    
    # Inform user if the requested volume is being adjusted
    if cycles * increment != volume:
        actual_vol = cycles * increment
        machine.log.warning(f"Volume {volume}uL is not a multiple of {increment}uL. Dispensing {actual_vol}uL.")

    if cycles <= 0:
        send_problem(machine, f"Volume {volume}uL is too low to dispense; must be at least {increment}uL.")
        return 0
    else:
        machine.log.info(f"{cycles} cycles of pump {pump} will be applied to dispense {volume} uL.")
        return cycles

def calculate_angles(machine, pump_key, target_x, target_y):
    """
    Returns angles needed for centering the end effector or a pump over the designated target
    """

    # Determine if centering the end effector or a pump
    pump = None
    if pump_key is not None and pump_key != 0 and pump_key != "0":
        # A number (1,2,3,4) or pump string ("p1", "p2", "p3", "p4") is valid
        pump = f"p{pump_key}" if isinstance(pump_key,int) else str(pump_key).lower()

    if pump:
        # If offsets cannot be found, then bail since pump_key was not valid
        pump_offset = machine.config['pump_offsets'].get(pump)
        dx = pump_offset['dx']
        dy = pump_offset['dy']
        if pump_offset is None:
            send_problem(machine, f"Invalid pump specified: '{pump_key}'.")
            return None
        
        # Pump Offset logic: Guess and Refine
        machine.log.info(f"Starting 2-pass move for pump '{pump}'...")
        machine.log.info(f" -> Estimating orientation for center ({target_x}, {target_y}).")
        guessed_angles = kinematics.inverse_kinematics(machine, target_x, target_y)
        if guessed_angles is None:
            send_problem(machine, "Target position is likely unreachable (IK Pass 1 failed).")
            return None
        
        _theta1_guess, theta2_guess = guessed_angles
        machine.log.info(f" -> Estimated orientation angle (theta2) = {theta2_guess:.2f} degrees.")

        orientation_rad = math.radians(theta2_guess)
        cos_theta = math.cos(orientation_rad)
        sin_theta = math.sin(orientation_rad)

        x_offset_rotated = dx * cos_theta - dy * sin_theta
        y_offset_rotated = dx * sin_theta + dy * cos_theta

        x_center_target = target_x + x_offset_rotated
        y_center_target = target_y + y_offset_rotated

        machine.log.info(f" -> Corrected center target is ({x_center_target:.3f}, {y_center_target:.3f}).")
        machine.log.info(f"Solving final IK for corrected center target.")
        target_angles = kinematics.inverse_kinematics(machine, x_center_target, y_center_target)
    else:
        machine.log.info(f"IK request for (x={target_x}, y={target_y})...")
        target_angles = kinematics.inverse_kinematics(machine, target_x, target_y)

    # Log an error but carry on
    if target_angles is None:
        machine.log.error("Inverse kinematics failed at end of `calculate_angles`")
    
    return target_angles


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@try_wrapper    
def handle_home(machine, payload):
    # Monolithic and needs updating, but this method works, so refactoring not a high priority
    machine.log.info("Home command received.")
    machine.go_to_state('Homing')

@try_wrapper
def handle_move_to(machine, payload):
    """
    Handles the high-level 'move_to' command. It uses inverse kinematics
    to convert Cartesian coordinates into motor steps.
    No calibration is performed with this routine. Position is where the sidekick 
    thinks the world coordinates are.
    """
    # 1. Guard Condition: Check if homed
    if not check_homed(machine):
        return

    # 2. Extract and Validate Input Arguments
    args = payload.get("args", {})

    target_x = args.get("x")
    target_y = args.get("y")
    pump_arg = args.get("pump")

    if target_x is None or target_y is None:
        send_problem(machine, "Missing 'x' or 'y' in command arguments.")
        return

    try:
        target_x = float(target_x)
        target_y = float(target_y)
    except ValueError:
        send_problem(machine, "Invalid coordinate format; 'x' and 'y' must be numbers.")
        return

    # 3. Perform Inverse Kinematics
    machine.log.info(f"IK request for (x={target_x}, y={target_y}, pump={pump_arg})...")
    target_angles = calculate_angles(machine, pump_arg, target_x, target_y)

    # 4. Check for IK Failure
    if target_angles is None:
        # The IK function already logged the specific error.
        send_problem(machine, "Inverse kinematics failed. Target may be unreachable or out of safe limits.")
        return
    
    theta1, theta2 = target_angles

    # 5. Convert Validated Angles to Steps
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)
    machine.log.info(f"IK success. Target: ({theta1:.2f}, {theta2:.2f}) degrees -> ({target_m1_steps}, {target_m2_steps}) steps.")

    # 6. Set Flags and Execute Move
    sequence = [{"state":"Moving"}]
    context = {
        "name":"move_to",
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context = context)

@try_wrapper
def handle_move_rel(machine, payload):
    """
    Handles the 'move_rel' command. Moves the arm relative to its
    current position by a Cartesian offset (dx, dy).
    """
    # 1. Guard Condition: Check if homed
    if not check_homed(machine):
        return

    # 2. Extract and Validate Input Arguments
    args = payload.get("args", {})
    dx = args.get("dx")
    dy = args.get("dy")

    if dx is None or dy is None:
        send_problem(machine, "Missing 'dx' or 'dy' in command arguments.")
        return

    try:
        dx = float(dx)
        dy = float(dy)
    except ValueError:
        send_problem(machine, "Invalid offset format; 'dx' and 'dy' must be numbers.")
        return

    # 3. Get Current Cartesian Position using Forward Kinematics
    # This is the key step for a relative move.
    current_m1_steps = machine.flags.get('current_m1_steps', 0)
    current_m2_steps = machine.flags.get('current_m2_steps', 0)
    
    current_theta1, current_theta2 = kinematics.steps_to_degrees(machine, current_m1_steps, current_m2_steps)
    x_current, y_current = kinematics.forward_kinematics(machine, current_theta1, current_theta2)
    
    machine.log.info(f"Current position: ({x_current:.3f}, {y_current:.3f})cm. Applying offset ({dx}, {dy}).")

    # 4. Calculate Target Cartesian Position
    x_target = x_current + dx
    y_target = y_current + dy

    # 5. Convert Target Position back to Motor Steps using Inverse Kinematics
    target_angles = kinematics.inverse_kinematics(machine, x_target, y_target)

    if target_angles is None:
        send_problem(machine, f"Inverse kinematics failed. Target ({x_target:.2f}, {y_target:.2f}) may be unreachable.")
        return
    
    theta1_target, theta2_target = target_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1_target, theta2_target)
    
    # 6. Set Context and Start the Sequencer
    sequence = [{"state": "Moving"}]
    context = {
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context=context)

#@try_wrapper
def handle_dispense(machine, payload):
    """
    Dispenses a specified volume from a pump at the current arm location.
    This command uses the state sequencer to execute the dispense action.
    """
    if not check_homed(machine): return
    
    # 1. Extract and Validate Arguments
    args = payload.get('args',{})
    pump = args.get('pump')
    vol = args.get('vol',None)
    
    if pump not in machine.config['pump_offsets']:
        valid_pumps = list(machine.config["pump_offsets"].keys())
        send_problem(machine, f"Invalid pump specified: {pump}. Choose from {valid_pumps}")
        return

    if vol is None:
        send_problem(machine, "Missing 'vol' in command arguments.")
        return

    # 2. Calculate Dispense Cycles
    cycles = calculate_dispense_cycles(machine, vol, pump)
        
    # 3. Set Context and Start the Sequencer
    machine.log.info(f"Dispense command accepted for pump {pump}, {cycles} cycles.")
    
    sequence = [{"state": "Dispensing"}]
    context = {
        "name": "dispense",
        "dispense_pump": pump,
        "dispense_cycles": cycles
    }
    machine.sequencer.start(sequence, initial_context=context)

#@try_wrapper
def handle_dispense_at(machine, payload):
    """
    Moves a specific pump tip to an absolute (x, y) coordinate, then
    dispenses a specified volume. This is a multi-step sequence.
    """
    if not check_homed(machine): return

    # 1. Extract and Validate All Arguments
    args = payload.get("args", {})
    target_x = args.get("x")
    target_y = args.get("y")
    pump_arg = args.get("pump")
    vol = args.get("vol")
    # Handle the two accepted forms (str|int) of pump argument
    pump = f"p{pump_arg}" if isinstance(pump_arg,int) else str(pump_arg).lower()

    if target_x is None or target_y is None or pump_arg is None or vol is None:
        send_problem(machine, "Missing 'x', 'y', 'pump', or 'vol' in command arguments.")
        return

    pump_offset = machine.config['pump_offsets'].get(pump)
    if pump_offset is None:
        send_problem(machine, f"Invalid pump key '{pump}'.")
        return

    # Perform Inverse Kinematics
    machine.log.info(f"IK request from dispense_at for (x={target_x}, y={target_y}, pump={pump})...")
    target_angles = calculate_angles(machine, pump, target_x, target_y)
    
    if target_angles is None:
        send_problem(machine, "Target position is unreachable (IK Pass 2 failed).")
        return
    
    theta1, theta2 = target_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)
    machine.log.info(f"IK success. Target: ({theta1:.2f}, {theta2:.2f}) degrees -> ({target_m1_steps}, {target_m2_steps}) steps.")

    # --- 3. Calculate the Dispense (Logic from handle_dispense) ---
    cycles = calculate_dispense_cycles(machine, vol, pump)

    # --- 4. Build the Sequence and Context ---
    # The context must contain ALL information needed for ALL steps in the sequence.
    machine.log.info(f"Dispense_at command accepted. Moving tip {pump} to ({target_x}, {target_y}) then dispensing {cycles} cycles.")
    
    sequence = [
        {"state": "Moving"},
        {"state": "Dispensing"}
    ]
    context = {
        "name": "dispense_at",
        # Parameters for the 'Moving' state
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps,
        # Parameters for the 'Dispensing' state
        "dispense_pump": pump,
        "dispense_cycles": cycles
    }

    # --- 5. Start the Sequencer ---
    machine.sequencer.start(sequence, initial_context=context)

@try_wrapper
def handle_steps(machine, payload):
    """
    Handles the low-level 'steps' command for relative motor movement.
    """
    # Must be homed to work properly
    if not check_homed(machine): return

    # 1. Extract and Validate Arguments
    args = payload.get("args", {})
    m1_rel_steps = args.get("m1", 0)
    m2_rel_steps = args.get("m2", 0)

    try:
        m1_rel_steps = int(m1_rel_steps)
        m2_rel_steps = int(m2_rel_steps)
    except (ValueError, TypeError):
        send_problem(machine, "Invalid step format; 'm1' and 'm2' must be integers.")
        return

    # 2. Calculate the absolute target position from the current position
    current_m1 = machine.flags.get('current_m1_steps', 0)
    current_m2 = machine.flags.get('current_m2_steps', 0)
    
    target_m1 = current_m1 + m1_rel_steps
    target_m2 = current_m2 + m2_rel_steps

    machine.log.info(f"Steps command accepted. Moving relatively by ({m1_rel_steps}, {m2_rel_steps}) to absolute ({target_m1}, {target_m2}).")
    
    # 3. Set Context and Start the Sequencer
    sequence = [{"state": "Moving"}]
    context = {
        "name": "steps",
        "target_m1_steps": target_m1,
        "target_m2_steps": target_m2
    }
    machine.sequencer.start(sequence, initial_context=context)

def handle_to_well(machine, payload):
    """
    Moves end effector to a specified well on a 96-well plate using a fixed A1 offset.
    """
    if not check_homed(machine):
        return

    # 1. Extract and Validate Arguments
    args = payload.get("args", {})
    well_designation = args.get("well")
    pump_arg = args.get("pump") # Can be None, 0, 1, "p1", etc.

    if well_designation is None:
        send_problem(machine, "Missing required 'well' argument.")
        return

    # 2. Parse well designation to grid indices
    parsed_indices = parse_well_designation(machine, well_designation)
    if parsed_indices is None:
        send_problem(machine, f"Invalid 'well' designation: '{well_designation}'.")
        return
    row_idx, col_idx = parsed_indices

    # 3. Calculate Well Coordinates (Plate Relative)
    pitch = machine.config['plate_geometry']['well_pitch_cm']
    
    # Note: Ensure these axes match your physical setup. 
    # Based on previous code: x=Rows, y=Cols
    well_x_rel = row_idx * pitch
    well_y_rel = col_idx * pitch
    
    # 4. Apply A1 Offset (Transform to World Coordinates)
    a1_offset = machine.config.get('A1_offset', {'dx': 0, 'dy': 0})
    target_x = well_x_rel + a1_offset['dx']
    target_y = well_y_rel + a1_offset['dy']

    machine.log.info(f"Targeting '{well_designation}': Rel({well_x_rel:.2f}, {well_y_rel:.2f}) -> World({target_x:.2f}, {target_y:.2f})")

    # 5. Inverse Kinematics (Handles Pump Offsets if pump_arg is provided)
    target_angles = calculate_angles(machine, pump_arg, target_x, target_y)
    if target_angles is None:
        send_problem(machine, "Inverse kinematics failed. Target may be unreachable.")
        return
    
    theta1, theta2 = target_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)

    # 6. Execute Move
    sequence = [{"state":"Moving"}]
    context = {
        "name": "move_to",
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context=context)


def handle_to_well_with_pumps(machine, payload):
    """
    Moves the end effector or a specific pump to a specified well using fixed A1 offset.
    Optionally dispenses if 'vol' is provided.
    """
    if not check_homed(machine):
        return

    # 1. Extract and Validate Arguments
    args = payload.get("args", {})
    well_designation = args.get("well")
    pump_arg = args.get("pump") 
    vol = args.get("vol")

    if well_designation is None:
        send_problem(machine, "Missing required 'well' argument.")
        return
    
    if vol is not None and pump_arg is None:
        send_problem(machine, "Missing 'pump' argument; required when 'vol' is provided.")
        return

    # 2. Parse well designation
    parsed_indices = parse_well_designation(machine, well_designation)
    if parsed_indices is None:
        send_problem(machine, f"Invalid 'well' designation: '{well_designation}'.")
        return
    row_idx, col_idx = parsed_indices

    # 3. Calculate Target Coordinates (World Space)
    pitch = machine.config['plate_geometry']['well_pitch_cm']
    a1_offset = machine.config.get('A1_offset', {'dx': 0, 'dy': 0})
    
    target_x = (row_idx * pitch) + a1_offset['dx']
    target_y = (col_idx * pitch) + a1_offset['dy']

    machine.log.info(f"Targeting '{well_designation}': World({target_x:.2f}, {target_y:.2f})")

    # 4. Inverse Kinematics
    target_angles = calculate_angles(machine, pump_arg, target_x, target_y)
    if target_angles is None:
        send_problem(machine, "Inverse kinematics failed. Target may be unreachable.")
        return
    
    theta1, theta2 = target_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)

    # 5. Build Sequence (Move only OR Move + Dispense)
    if vol is not None:
        pump = f"p{pump_arg}" if isinstance(pump_arg, int) else str(pump_arg).lower()
        cycles = calculate_dispense_cycles(machine, vol, pump)
        
        if cycles <= 0: return # Error already sent by calc function

        sequence = [
            {"state": "Moving"},
            {"state": "Dispensing"}
        ]
        context = {
            "name": "to_well_and_dispense",
            "target_m1_steps": target_m1_steps,
            "target_m2_steps": target_m2_steps,
            "dispense_pump": pump,
            "dispense_cycles": cycles
        }
    else:
        sequence = [{"state": "Moving"}]
        context = {
            "name": "to_well",
            "target_m1_steps": target_m1_steps,
            "target_m2_steps": target_m2_steps
        }

    machine.sequencer.start(sequence, initial_context=context)

```

### `kinematics.py`

```python
# firmware/sidekick/kinematics.py
# Kinematics calculations for the Sidekick SCARA arm.
# Adapted from the original procedural code.
# type: ignore
import math

# ============================================================================
# UTILITY AND CONVERSION FUNCTIONS
# ============================================================================

def steps_to_degrees(machine, m1_steps, m2_steps):
    """Converts absolute motor steps to angles in degrees."""
    # TODO: Should simplify to steps * cfg['step_angle_degrees'] / cfg['microsteps']

    cfg = machine.config['motor_settings']
    steps_per_rev = (360 / cfg['step_angle_degrees']) * cfg['microsteps']
    
    theta1 = (m1_steps / steps_per_rev) * 360
    theta2 = (m2_steps / steps_per_rev) * 360
    return theta1, theta2

def degrees_to_steps(machine, theta1, theta2):
    """Converts motor angles in degrees to absolute step counts."""
    cfg = machine.config['motor_settings']
    steps_per_rev = (360 / cfg['step_angle_degrees']) * cfg['microsteps']
    
    m1_steps = int((theta1 / 360) * steps_per_rev)
    m2_steps = int((theta2 / 360) * steps_per_rev)
    return m1_steps, m2_steps

# ============================================================================
# CORE KINEMATICS LOGIC (Adapted from kinematicsfunctions.py)
# ============================================================================

def _find_standard_position_angle(point):
    """Calculates the angle of a vector in a 360-degree system."""
    x, y = point[0], point[1]
    if x == 0:
        return 90 if y > 0 else 270
    
    ref_angle = math.degrees(math.atan(y / x))
    
    if x > 0 and y >= 0: quadrant = 1 # Q1
    elif x < 0 and y >= 0: quadrant = 2 # Q2
    elif x < 0 and y < 0: quadrant = 3 # Q3
    else: quadrant = 4 # Q4

    if quadrant == 1: return ref_angle
    if quadrant == 2 or quadrant == 3: return 180 + ref_angle
    if quadrant == 4: return 360 + ref_angle

def _get_intersections(x0, y0, r0, x1, y1, r1):
    """Calculates the intersection points of two circles."""
    d = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)

    if d > r0 + r1 or d < abs(r0 - r1) or d == 0:
        return None  # No solution

    a = (r0**2 - r1**2 + d**2) / (2 * d)
    h = math.sqrt(r0**2 - a**2)
    x2 = x0 + a * (x1 - x0) / d
    y2 = y0 + a * (y1 - y0) / d

    x3 = x2 + h * (y1 - y0) / d
    y3 = y2 - h * (x1 - x0) / d
    x4 = x2 - h * (y1 - y0) / d
    y4 = y2 + h * (x1 - x0) / d
    return (x3, y3, x4, y4)

def inverse_kinematics(machine, target_x, target_y):
    """
    Calculates the required motor angles (theta1, theta2) to reach a
    Cartesian coordinate (target_x, target_y).
    
    Returns a tuple (theta1, theta2) on success, or None on failure.
    """

    # # Apply calibration transformation
    # corrected_x, corrected_y = apply_calibration_transform(machine, target_x, target_y)
    
    # # Log the transformation for debugging, but only if a change occurred.
    # if abs(target_x - corrected_x) > 0.001 or abs(target_y - corrected_y) > 0.001:
    #     machine.log.info(f"Calibration applied: ({target_x:.3f}, {target_y:.3f}) -> ({corrected_x:.3f}, {corrected_y:.3f})")
    # else:
    #     machine.log.info("Calibration was not needed")

    # # Update the local variables to use the corrected values.
    # target_x, target_y = corrected_x, corrected_y

    # # -- Calibration complete --

    cfg = machine.config['kinematics']
    L1, L2, L3 = cfg['L1'], cfg['L2'], cfg['L3']
    op_limits = machine.config['operational_limits_degrees']

    # The origin is assumed to be (0, 0)
    p4 = (target_x, target_y)
    
    # Find possible locations for joint P1 (elbow of the upper arm)
    p1_intersections = _get_intersections(p4[0], p4[1], L3, 0, 0, L1)
    if p1_intersections is None:
        machine.log.error("IK Error: Target coordinate is physically unreachable.")
        return None

    # Two possible arm conformations exist. We must check which is valid.
    p1a = (p1_intersections[0], p1_intersections[1])
    p1b = (p1_intersections[2], p1_intersections[3])
    
    possible_solutions = []

    for p1 in [p1a, p1b]:
        # Calculate theta1 for this conformation
        theta1 = _find_standard_position_angle(p1)
        
        # Calculate the vector for the lower arm linkage
        p3_vector = (p4[0] - p1[0], p4[1] - p1[1])
        p3_angle = _find_standard_position_angle(p3_vector)
        
        # The joint P2 is parallel to P3, but offset by L2
        # We find its position by moving backwards from the origin along the p3_angle
        p2_x = 0 + L2 * math.cos(math.radians(p3_angle + 180))
        p2_y = 0 + L2 * math.sin(math.radians(p3_angle + 180))
        
        # Calculate theta2 for this conformation
        theta2 = _find_standard_position_angle((p2_x, p2_y))
        
        # # *** Angle calibration attempt
        # corrected_theta1, corrected_theta2 = apply_angle_calibration_transform(machine, theta1, theta2)
        
        # # Log the change for debugging.
        # if abs(theta1 - corrected_theta1) > 0.01 or abs(theta2 - corrected_theta2) > 0.01:
        #     machine.log.info(f"Angle Calib Applied: ({theta1:.2f}, {theta2:.2f}) -> ({corrected_theta1:.2f}, {corrected_theta2:.2f})")
        # else:
        #     machine.log.info(f"No Angle calibration needed")

        # # The rest of the checks will now use the corrected angles.
        # theta1, theta2 = corrected_theta1, corrected_theta2
        # # *** End angle calibration attempt        

        # Safety Check: Is this solution within operational limits?
        if (op_limits['m1_min'] <= theta1 <= op_limits['m1_max'] and
            op_limits['m2_min'] <= theta2 <= op_limits['m2_max']):
            possible_solutions.append((theta1, theta2))

    if not possible_solutions:
        machine.log.error("IK Error: All solutions violate operational angle limits.")
        return None
    
    # If multiple solutions are valid, prefer the first one (elbow-back).
    # More advanced logic could choose the one requiring less travel.
    return possible_solutions[0]

def forward_kinematics(machine, theta1, theta2):
    """
    Calculates the Cartesian coordinate (x, y) of the arm's center
    given the motor angles (theta1, theta2).

    This version correctly models the five-bar parallel SCARA linkage
    by enforcing the geometric constraints derived from the inverse_kinematics function.
    """
    cfg = machine.config['kinematics']
    L1, L3 = cfg['L1'], cfg['L3']

    # Convert angles to radians for math functions
    theta1_rad = math.radians(theta1)
    theta2_rad = math.radians(theta2)

    # 1. Find the position of the primary elbow joint (p1).
    p1_x = L1 * math.cos(theta1_rad)
    p1_y = L1 * math.sin(theta1_rad)
    
    # 2. The core constraint of this linkage is that the vector from p1 to p4
    #    is parallel to the vector from the origin to p2, but points in the
    #    opposite direction. Therefore, its angle is theta2 + 180 degrees.
    #    cos(t + 180) = -cos(t)
    #    sin(t + 180) = -sin(t)
    #    So, the vector (p1->p4) can be calculated directly.
    vec_p1_p4_x = -L3 * math.cos(theta2_rad)
    vec_p1_p4_y = -L3 * math.sin(theta2_rad)

    # 3. The final position (p4) is the position of p1 plus the vector from p1 to p4.
    p4_x = p1_x + vec_p1_p4_x
    p4_y = p1_y + vec_p1_p4_y
    
    return (p4_x, p4_y)
```

### `states.py`

```python
# firmware/sidekick/states.py
# type: ignore
import time
import digitalio
from shared_lib.statemachine import State
from shared_lib.messages import Message
from firmware.common.common_states import listen_for_instructions
from . import kinematics

class Initialize(State):
    @property
    def name(self): return 'Initialize'
    def enter(self, machine, context=None):
        super().enter(machine, context)
        try:
            # Create a dictionary of all hardware objects for easy access
            machine.hardware = {}
            pin_config = machine.config['pins']
            
            # Setup Motors and Endstops
            for i in [1, 2]:
                machine.hardware[f'motor{i}_step'] = digitalio.DigitalInOut(pin_config[f'motor{i}_step'])
                machine.hardware[f'motor{i}_step'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_dir'] = digitalio.DigitalInOut(pin_config[f'motor{i}_dir'])
                machine.hardware[f'motor{i}_dir'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_enable'] = digitalio.DigitalInOut(pin_config[f'motor{i}_enable'])
                machine.hardware[f'motor{i}_enable'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_enable'].value = True # Start with motors disabled (HIGH = off for some drivers)

                machine.hardware[f'endstop_m{i}'] = digitalio.DigitalInOut(pin_config[f'endstop_m{i}'])
                machine.hardware[f'endstop_m{i}'].direction = digitalio.Direction.INPUT
                machine.hardware[f'endstop_m{i}'].pull = digitalio.Pull.UP
            
            # Setup Pumps
            machine.hardware['pumps'] = {}
            for i in [1, 2, 3, 4]:
                machine.hardware['pumps'][f'p{i}'] = digitalio.DigitalInOut(pin_config[f'pump{i}'])
                machine.hardware['pumps'][f'p{i}'].direction = digitalio.Direction.OUTPUT

            machine.log.info("Sidekick hardware initialized successfully.")
            
        except Exception as e:
            machine.flags['error_message'] = f"Hardware Initialization failed: {e}"
            machine.go_to_state('Error')
        
        machine.go_to_state('Homing') # The first action after init must be to home.

class Idle(State):
    @property
    def name(self): return 'Idle'
    def __init__(self, telemetry_callback=None):
        super().__init__()
        self._telemetry_callback = telemetry_callback
    def enter(self, machine, context=None):
        super().enter(machine, context)
        self._telemetry_interval = machine.flags.get('telemetry_interval', 5.0)
        self._next_telemetry_time = time.monotonic() + self._telemetry_interval
        machine.hardware['motor1_enable'].value = False 
        machine.hardware['motor2_enable'].value = False
    def update(self, machine):
        super().update(machine)
        listen_for_instructions(machine)
        if time.monotonic() >= self._next_telemetry_time:
            if self._telemetry_callback:
                self._telemetry_callback(machine)
            self._next_telemetry_time = time.monotonic() + self._telemetry_interval

class Homing(State):
    """
    Homing procedure
    """
    @property
    def name(self): return 'Homing'

    def enter(self, machine, context=None):
        super().enter(machine,context)
        machine.log.info("Starting corrected homing routine...")
        machine.flags['is_homed'] = False

        # Load settings
        self._backoff_steps = machine.config['homing_settings']['joint_backoff_steps']
        self._max_homing_steps = machine.config['safe_limits']['m1_max_steps'] + 2000
        
        # Internal state management
        self._homing_stage = 'START_M1'
        self._steps_taken = 0
        self._step_delay = 1 / machine.config['motor_settings']['max_speed_sps']
        self._next_step_time = time.monotonic()

        machine.hardware['motor1_enable'].value = False
        machine.hardware['motor2_enable'].value = False

    def update(self, machine):
        super().update(machine)

        # --- Phase 1: Home M1 (CW) ---
        if self._homing_stage == 'START_M1':
            machine.log.info("Phase 1: Homing Motor 1 (CW) with M2 disabled.")
            machine.hardware['motor2_enable'].value = True
            machine.hardware['motor1_dir'].value = True
            self._steps_taken = 0
            self._homing_stage = 'RUNNING_M1'

        elif self._homing_stage == 'RUNNING_M1':
            if not machine.hardware['endstop_m1'].value:
                # ABSOLUTE POSITION DEFINED
                
                machine.flags['current_m1_steps'] = 0 # step offset added later
                machine.log.info(f"M1 endstop reached. Position DEFINED as {machine.flags['current_m1_steps']} steps.")
                self._homing_stage = 'START_M2_JOINT'
                return
            
            # (Pulse and timeout logic remains the same)
            if time.monotonic() >= self._next_step_time:
                step_pin = machine.hardware['motor1_step']
                step_pin.value = True; step_pin.value = False
                self._steps_taken += 1
                self._next_step_time = time.monotonic() + self._step_delay
            if self._steps_taken > self._max_homing_steps:
                machine.flags['error_message'] = "FAULT: Homing timeout on Motor 1!"
                machine.go_to_state('Error')

        # --- Phase 2: Joint move to find M2 endstop (CCW) ---
        elif self._homing_stage == 'START_M2_JOINT':
            machine.log.info("Phase 2: Joint CCW move to find M2 endstop.")
            machine.hardware['motor2_enable'].value = False
            machine.hardware['motor1_dir'].value = False
            machine.hardware['motor2_dir'].value = False
            self._steps_taken = 0 # Timeout counter
            self._homing_stage = 'RUNNING_M2_JOINT'

        elif self._homing_stage == 'RUNNING_M2_JOINT':
            if not machine.hardware['endstop_m2'].value:
                # ABSOLUTE POSITION DEFINED
                step_offset = machine.config.get('step_correction', {'m1e':0, 'm2e':0})
                machine.flags['current_m2_steps'] = 1600 + step_offset['m2e'] # We know M2 is 1600 steps from M1 at the endstop, so we use that as our reference point.
                # M1's position is its starting point (0) plus the steps taken in this phase
                machine.flags['current_m1_steps'] = step_offset['m1e'] + self._steps_taken
                machine.log.info(f"M2 endstop reached. Positions DEFINED as M1={machine.flags['current_m1_steps']}, M2={machine.flags['current_m2_steps']}.")
                self._homing_stage = 'START_JOINT_BACKOFF'
                return

            # (Pulse and timeout logic remains the same)
            if time.monotonic() >= self._next_step_time:
                m1_pin = machine.hardware['motor1_step']; m2_pin = machine.hardware['motor2_step']
                m1_pin.value = True; m2_pin.value = True
                m1_pin.value = False; m2_pin.value = False
                self._steps_taken += 1
                self._next_step_time = time.monotonic() + self._step_delay
            if self._steps_taken > self._max_homing_steps:
                machine.flags['error_message'] = "FAULT: Homing timeout on M2 joint move!"
                machine.go_to_state('Error')

        # --- Phase 3: Back off the endstop ---
        elif self._homing_stage == 'START_JOINT_BACKOFF':
            machine.log.info(f"Phase 3: Backing off endstop with joint move (CW) for {self._backoff_steps} steps.")
            machine.hardware['motor1_dir'].value = True
            machine.hardware['motor2_dir'].value = True
            self._steps_taken = self._backoff_steps
            self._homing_stage = 'RUNNING_JOINT_BACKOFF'

        elif self._homing_stage == 'RUNNING_JOINT_BACKOFF':
            if self._steps_taken > 0:
                # (Backoff pulse logic remains the same)
                 if time.monotonic() >= self._next_step_time:
                    m1_pin = machine.hardware['motor1_step']; m2_pin = machine.hardware['motor2_step']
                    m1_pin.value = True; m2_pin.value = True
                    m1_pin.value = False; m2_pin.value = False
                    self._steps_taken -= 1
                    self._next_step_time = time.monotonic() + self._step_delay
            else:
                # --- CORRECTED POSITION UPDATE ---
                # The new position is the old position MINUS the backoff steps.
                machine.flags['current_m1_steps'] -= self._backoff_steps
                machine.flags['current_m2_steps'] -= self._backoff_steps
                machine.log.info(f"Back-off complete. Final positions UPDATED to: M1={machine.flags['current_m1_steps']}, M2={machine.flags['current_m2_steps']}.")
                self._homing_stage = 'PREPARE_SAFE_MOVE'

        # --- Final Phase: Prepare for Safe Move (Logic is the same) ---
        elif self._homing_stage == 'PREPARE_SAFE_MOVE':
            machine.log.info("Physical homing successful. Calculating park position move.")
            machine.flags['is_homed'] = True
            
            # Read the absolute park coordinates from the config
            park_x = machine.config['homing_settings']['park_move_x']
            park_y = machine.config['homing_settings']['park_move_y']
            
            # Use inverse kinematics to find the angles for the park position
            target_angles = kinematics.inverse_kinematics(machine, park_x, park_y)
            
            if target_angles is None:
                # This should not happen if the park position is well-chosen, but it's a critical safety check.
                machine.flags['error_message'] = f"FATAL: Park position ({park_x}, {park_y}) is unreachable."
                machine.go_to_state('Error')
                return

            theta1, theta2 = target_angles
            target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)

            machine.log.info(f"Target park pos: (x={park_x}, y={park_y}) -> (m1={target_m1_steps}, m2={target_m2_steps}) steps.")

            # Set the flags for the 'Moving' state
            machine.flags['target_m1_steps'] = target_m1_steps
            machine.flags['target_m2_steps'] = target_m2_steps
            machine.flags['on_move_complete'] = 'Idle'

            # Send success message to host *before* starting the move
            response = Message.create_message(
                subsystem_name=machine.name, status="SUCCESS",
                payload={"detail": "Homing successful. Moving to park position."}
            )
            machine.postman.send(response.serialize())
            machine.go_to_state('Moving')

    def exit(self, machine):
        super().exit(machine)
        
class Moving(State):
    """
    The 'Motion Engine' state. It executes a planned move from a start point
    to a target point in a non-blocking way.
    """
    @property
    def name(self): return 'Moving'

    def enter(self, machine, context=None):
        """
        Called once on entry. This is where we plan the entire move.
        """
        super().enter(machine,context)
        
        # 1. Read start and target positions from the machine's flags
        start_m1 = machine.flags['current_m1_steps']
        start_m2 = machine.flags['current_m2_steps']
        self.target_m1 = machine.sequencer.context.get('target_m1_steps',
            machine.flags.get('target_m1_steps'))
        self.target_m2 = machine.sequencer.context.get('target_m2_steps',
            machine.flags.get('target_m2_steps'))
        
        machine.log.info(f"Moving from ({start_m1}, {start_m2}) to ({self.target_m1}, {self.target_m2}).")

        # 2. Calculate the plan: steps and direction for each motor
        delta_m1 = self.target_m1 - start_m1
        delta_m2 = self.target_m2 - start_m2
        
        self.steps_left_m1 = abs(delta_m1)
        self.steps_left_m2 = abs(delta_m2)
        
        # Set motor direction pins (True/False may need to be adjusted for your wiring)
        machine.hardware['motor1_dir'].value = False if delta_m1 > 0 else True
        # Is this stepper backwards?
        machine.hardware['motor2_dir'].value = False if delta_m2 > 0 else True

        # 3. Enable the motors
        machine.hardware['motor1_enable'].value = False
        machine.hardware['motor2_enable'].value = False
        time.sleep(0.01) # Short delay to ensure drivers are fully enabled

    def update(self, machine):
        """
        Called on every loop. This is the core stepper pulse generator.
        This is a simple implementation that steps both motors on each loop.
        A more advanced version would use Bresenham's algorithm for smoother lines.
        """
        super().update(machine)
        
        # Check for unexpected endstops (Safety First!)
        # Note: Endstop value is False when pressed due to Pull.UP
        if not machine.hardware['endstop_m1'].value or not machine.hardware['endstop_m2'].value:
            machine.hardware['motor1_enable'].value = True # Immediately disable motors
            machine.hardware['motor2_enable'].value = True
            machine.flags['is_homed'] = False # We no longer know our position
            machine.flags['error_message'] = "FAULT: Endstop triggered during move!"
            machine.go_to_state('Error')
            return # Stop processing immediately

        move_is_done = True
        
        # Pulse Motor 1 if it still has steps to go
        if self.steps_left_m1 > 0:
            step_pin = machine.hardware['motor1_step']
            step_pin.value = True
            step_pin.value = False # This pulse is very short
            self.steps_left_m1 -= 1
            move_is_done = False
        
        # Pulse Motor 2 if it still has steps to go
        if self.steps_left_m2 > 0:
            step_pin = machine.hardware['motor2_step']
            step_pin.value = True
            step_pin.value = False
            self.steps_left_m2 -= 1
            move_is_done = False
            
        # If both motors have completed their moves
        if move_is_done:
            # Update the final position in the machine's flags
            machine.flags['current_m1_steps'] = self.target_m1
            machine.flags['current_m2_steps'] = self.target_m2

            self.task_complete = True
            
    def exit(self, machine):
        super().exit(machine)

class Dispensing(State):
    @property
    def name(self): return 'Dispensing'

    def enter(self, machine, context=None):
        super().enter(machine, context)

        # Read parameters from the sequencer context first, falling back to machine flags
        # for compatibility if needed. This makes the state work with the new handlers.
        self.pump_key = machine.sequencer.context.get('dispense_pump', 
            machine.flags.get('dispense_pump'))
        self.cycles_left = machine.sequencer.context.get('dispense_cycles', 
            machine.flags.get('dispense_cycles'))

        # Check that parameters were successfully loaded
        if self.pump_key is None or self.cycles_left is None:
            machine.flags['error_message'] = "Dispensing state entered without pump or cycle info."
            machine.go_to_state('Error')
            return

        self.pump_pin = machine.hardware['pumps'][self.pump_key]
        self.pump_state = 'aspirating'
        self.timings = machine.config['pump_timings']
        
        machine.log.info(f"Dispensing {self.cycles_left} cycles from {self.pump_key}.")
        # Start the first aspirate cycle
        self.pump_pin.value = True
        self._next_toggle_time = time.monotonic() + self.timings['aspirate_time']

    def update(self, machine):
        super().update(machine)
        if time.monotonic() >= self._next_toggle_time:
            if self.pump_state == 'aspirating':
                self.pump_pin.value = False
                self.pump_state = 'dispensing'
                self._next_toggle_time = time.monotonic() + self.timings['dispense_time']
                self.cycles_left -= 1
            elif self.pump_state == 'dispensing':
                if self.cycles_left > 0:
                    self.pump_pin.value = True
                    self.pump_state = 'aspirating'
                    self._next_toggle_time = time.monotonic() + self.timings['aspirate_time']
                else:
                    # We are finished
                    machine.log.info("Dispense complete.")
                   
                    # Instead of transitioning directly, we mark the task as complete
                    # for the sequencer.
                    self.task_complete = True

    def exit(self, machine):
        super().exit(machine)
        # Ensure the pump is off when we leave the state
        if hasattr(self, 'pump_pin'):
            self.pump_pin.value = False
```

