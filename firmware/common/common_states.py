# firmware/common/common_states.py
# This file contains generic, reusable states for any device.
#type: ignore
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

    def enter(self, machine):
        super().enter(machine)
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
    
    def enter(self, machine):
        super().enter(machine)
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

    def enter(self, machine):
        super().enter(machine)
        error_msg = machine.flags.get('error_message', "Unknown error.")
        machine.log.critical(f"ENTERING ERROR STATE: {error_msg}")

        # --- NEW: Hardware Setup ---
        # If a reset pin was provided during initialization, set it up.
        if self._reset_pin_config:
            try:
                self._reset_button = digitalio.DigitalInOut(self._reset_pin_config)
                self._reset_button.direction = digitalio.Direction.INPUT
                self._reset_button.pull = digitalio.Pull.UP
                machine.log.info(f"Error recovery button initialized on pin {str(self._reset_pin_config)}.")
            except Exception as e:
                # If the pin is invalid, log it but don't crash. The error state
                # will just become permanent, which is a safe fallback.
                machine.log.error(f"Could not initialize reset button: {e}")
                self._reset_button = None

        # This flag is for debouncing the button.
        self._button_is_pressed = False
        
        # Turn LED on solid to indicate a persistent error, if an LED exists
        if hasattr(machine, 'led'):
            machine.led.value = True

    def update(self, machine):
        """
        If a reset button is configured, this method checks for a press.
        Otherwise, it does nothing, requiring a power cycle to exit.
        """
        # --- NEW: Button Checking Logic ---
        # Only run this logic if the reset button was successfully initialized.
        if self._reset_button:
            # Button is active-low (value is False when pressed)
            button_value_is_low = not self._reset_button.value

            # Trigger on the "falling edge" (the moment it's pressed)
            if button_value_is_low and not self._button_is_pressed:
                self._button_is_pressed = True
                
                machine.log.warning(f"Reset button pressed. Acknowledging error and attempting to recover to '{self._reset_state_name}' state.")
                
                machine.flags['error_message'] = '' # Clear the error
                machine.go_to_state(self._reset_state_name)
            
            # Reset the debounce flag when the button is released
            elif not button_value_is_low:
                self._button_is_pressed = False
        
        # If no button is configured, the machine will just stay in this state.
        # A small sleep prevents this loop from consuming all CPU.
        time.sleep(0.1)