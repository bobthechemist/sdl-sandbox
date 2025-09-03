# firmware/common/common_states.py
# This file contains generic, reusable states for any device.
#type: ignore
import time
from shared_lib.statemachine import State
from shared_lib.messages import Message

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
        raw_message = machine.postman.receive()
        if raw_message:
            try:
                message = Message.from_json(raw_message)
                if message.status == "INSTRUCTION":
                    machine.handle_instruction(message.payload)
            except Exception as e:
                machine.log.error(f"Could not process message: '{raw_message}'. Error: {e}")

        # Trigger the telemetry callback at the correct interval
        if time.monotonic() >= self._next_telemetry_time:
            if self._telemetry_callback:
                self._telemetry_callback(machine)
            self._next_telemetry_time = time.monotonic() + self._telemetry_interval