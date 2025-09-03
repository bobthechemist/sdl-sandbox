# firmware/common/common_states.py
# This file contains generic, reusable states for any device.
#type: ignore
import time
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