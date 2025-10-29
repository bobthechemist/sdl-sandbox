# firmware/common/common_states.py
# This file contains generic, reusable states for any device.
# type: ignore
import time
import digitalio
from shared_lib.statemachine import State
from shared_lib.messages import Message

def listen_for_instructions(machine):
    """
    A reusable helper function that checks for and dispatches incoming
    INSTRUCTION messages. Any state can call this.
    """
    raw_message = machine.postman.receive()
    if raw_message:
        try:
            message = Message.from_json(raw_message)
            if message.status == "INSTRUCTION":
                machine.handle_instruction(message.payload)
        except Exception as e:
            machine.log.error(f"Could not process message: '{raw_message}'. Error: {e}")

class GenericIdle(State):
    """
    A generic, reusable Idle state. It handles listening for instructions
    and triggers a periodic, customizable telemetry broadcast.
    """
    @property
    def name(self):
        return 'Idle'

    def __init__(self, telemetry_callback=None):
        """
        Args:
            telemetry_callback (function, optional): A function that will be
                called to send the device's specific telemetry data.
        """
        super().__init__()
        self._telemetry_callback = telemetry_callback

    # <<< FIX IS HERE: Method signature updated to accept 'context'.
    def enter(self, machine, context=None):
        # <<< FIX IS HERE: Pass arguments to super().
        super().enter(machine, context)
        self._telemetry_interval = machine.flags.get('telemetry_interval', 5.0)
        self._next_telemetry_time = time.monotonic() + self._telemetry_interval

    def update(self, machine):
        super().update(machine)
        
        listen_for_instructions(machine)

        # Trigger the telemetry callback at the correct interval
        if time.monotonic() >= self._next_telemetry_time:
            if self._telemetry_callback:
                self._telemetry_callback(machine)
            self._next_telemetry_time = time.monotonic() + self._telemetry_interval

class GenericError(State):
    """
    A terminal state entered on critical failure (e.g., hardware init failed).
    """
    @property
    def name(self):
        return 'Error'
    
    # <<< FIX IS HERE: Method signature updated to accept 'context'.
    def enter(self, machine, context=None):
        # <<< FIX IS HERE: Pass arguments to super().
        super().enter(machine, context)
        error_msg = machine.flags.get('error_message', "Unknown error.")
        machine.log.critical(f"ENTERING ERROR STATE: {error_msg}")
        # Turn LED on solid to indicate a persistent error
        if hasattr(machine, 'led'):
            machine.led.value = True

    def update(self, machine):
        # Stay in this state until the device is reset
        time.sleep(10)

class GenericErrorWithButton(State):
    """
    A configurable, terminal state entered on critical failure.
    It can optionally be configured with a reset button that allows for
    manual recovery to a specified state.
    """
    @property
    def name(self):
        return 'Error'
    
    def __init__(self, reset_pin=None, reset_state_name='Idle'):
        """
        Initializes the GenericError state.

        Args:
            reset_pin (board.Pin, optional): The physical pin connected to a
                reset button. Must be a board pin object (e.g., board.GP20).
                If None, the error state is permanent until a power cycle.
            reset_state_name (str, optional): The name of the state to transition
                to when the reset button is pressed. Defaults to 'Idle'.
        """
        super().__init__()
        self._reset_pin_config = reset_pin
        self._reset_state_name = reset_state_name
        self._reset_button = None # This will hold the DigitalInOut object

    # <<< FIX IS HERE: Method signature updated to accept 'context'.
    def enter(self, machine, context=None):
        # <<< FIX IS HERE: Pass arguments to super().
        super().enter(machine, context)
        error_msg = machine.flags.get('error_message', "Unknown error.")
        machine.log.critical(f"ENTERING ERROR STATE: {error_msg}")
        # Abort any sequence
        machine.sequencer.abort("Entering error state")
        # --- Hardware Setup ---
        if self._reset_pin_config:
            try:
                self._reset_button = digitalio.DigitalInOut(self._reset_pin_config)
                self._reset_button.direction = digitalio.Direction.INPUT
                self._reset_button.pull = digitalio.Pull.UP
                machine.log.info(f"Error recovery button initialized on pin {str(self._reset_pin_config)}.")
            except ValueError as e:
                # Check if the error message indicates the pin is already in use.
                if "in use" in str(e).lower():
                    # This is expected behavior, log the message and carry on.
                    machine.log.info(f"Reset button on pin {str(self._reset_pin_config)} has already been initialized.")
                else:
                    # This is the unexpected behavior so log it and reraise the error
                    machine.log.error(f"Could not initialize reset button due to an unexpected runtime error: {e}")
                    self._reset_button = None
                    # raise TODO: Do we want to force the tool to abort? Perhaps a flag to turn this feature on and off?
            except Exception as e:
                machine.log.error(f"Could not initialize reset button: {e}")
                self._reset_button = None

        self._button_is_pressed = False
        
        if hasattr(machine, 'led'):
            machine.led.value = True

    def update(self, machine):
        """
        If a reset button is configured, this method checks for a press.
        """
        if self._reset_button:
            button_value_is_low = not self._reset_button.value

            if button_value_is_low and not self._button_is_pressed:
                self._button_is_pressed = True
                machine.log.warning(f"Reset button pressed. Recovering to '{self._reset_state_name}' state.")
                machine.flags['error_message'] = ''
                machine.go_to_state(self._reset_state_name)
            
            elif not button_value_is_low:
                self._button_is_pressed = False
        
        time.sleep(0.1)