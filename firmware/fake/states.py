# type: ignore
import time
import board
import digitalio
import analogio
from shared_lib.statemachine import State
from shared_lib.messages import Message
from shared_lib.command_library import CommonCommandHandler

# Constants for the state machine
ANALOG_READ_INTERVAL = 5.0  # seconds
BLINK_ON_TIME = 0.25        # seconds
BLINK_OFF_TIME = 0.25       # seconds

# This dictionary documents the device's capabilities.
SUPPORTED_COMMANDS = {
    "help": {
        "description": "Returns a list of all supported commands and their arguments.",
        "args": []
    },
    "blink": {
        "description": "Blinks the onboard LED a specified number of times.",
        "args": ["count (integer, default: 1)"]
    }
}


class Initialize(State):
    """
    Initializes the hardware (LED, ADC) required for the fake device.
    """
    @property
    def name(self):
        return 'Initialize'

    def enter(self, machine):
        super().enter(machine)
        # Setup hardware
        try:
            machine.led = digitalio.DigitalInOut(board.LED)
            machine.led.direction = digitalio.Direction.OUTPUT
            machine.led.value = False
            
            machine.analog_in = analogio.AnalogIn(board.A0)
            
            machine.log.info("Fake device initialized successfully.")
            machine.go_to_state('Idle')
        except Exception as e:
            # If any hardware is missing, go to a permanent error state
            machine.flags['error_message'] = str(e)
            machine.log.critical(f"Initialization failed: {e}")
            machine.go_to_state('Error')

class Idle(State):
    """
    The main operational state. It listens for incoming commands from the host
    and periodically sends back analog sensor readings.
    """
    @property
    def name(self):
        return 'Idle'

    def enter(self, machine):
        """Called once when entering the Idle state."""
        super().enter(machine)
        
        # --- THE FIX IS HERE ---
        # We must store the machine instance on self so that our
        # handler methods can access it.
        self.machine = machine
        
        self.next_analog_read_time = time.monotonic() + ANALOG_READ_INTERVAL
        machine.log.info("Entering Idle state. Listening for commands.")

        # Instantiate the common command handler
        self.common_command_handler = CommonCommandHandler(machine, SUPPORTED_COMMANDS)
        
        common_handlers = self.common_command_handler.get_handlers()
        
        device_specific_handlers = {
            "blink": self._handle_blink,
        }

        # Merge the dictionaries using a CircuitPython-compatible method.
        self.command_handlers = common_handlers.copy()
        self.command_handlers.update(device_specific_handlers)

    def update(self, machine):
        """Called on every loop while in the Idle state."""
        raw_message = machine.postman.receive()
        if raw_message:
            try:
                message = Message.from_json(raw_message)
                if message.status == "INSTRUCTION":
                    payload = message.payload
                    func_name = payload.get("func") if isinstance(payload, dict) else None
                    
                    handler = self.command_handlers.get(func_name, self._handle_unknown)
                    handler(payload) # Call the handler with just the payload

            except Exception as e:
                machine.log.error(f"Could not process message: '{raw_message}'. Error: {e}")

        # Send periodic analog data (unchanged)
        if time.monotonic() >= self.next_analog_read_time:
            analog_value = machine.analog_in.value
            heartbeat_message = Message.create_message(
                subsystem_name=machine.name, status="HEARTBEAT", payload={"analog_value": analog_value}
            )
            machine.postman.send(heartbeat_message.serialize())
            self.next_analog_read_time = time.monotonic() + ANALOG_READ_INTERVAL

    # --- Handlers ---
    
    def _handle_blink(self, payload):
        """Handles the 'blink' command."""
        try:
            count = int(payload.get("args", [1])[0])
        except (ValueError, IndexError):
            count = 1
        
        # Now this will work, because self.machine was set in enter()
        self.machine.flags['blink_count'] = count
        self.machine.log.info(f"Blink request received for {count} times.")
        self.machine.go_to_state('Blinking')

    def _handle_unknown(self, payload):
        """Handles any command not in our dispatcher dictionary."""
        func_name = payload.get("func") if payload else "N/A"
        self.machine.log.error(f"Received an unknown instruction: {func_name}")
        response = Message.create_message(
            subsystem_name=self.machine.name,
            status="PROBLEM",
            payload={"error": f"Unknown instruction: {func_name}"}
        )
        self.machine.postman.send(response.serialize())

class Blinking(State):
    """
    Handles the non-blocking logic for blinking the LED a set number of times.
    """
    @property
    def name(self):
        return 'Blinking'

    def enter(self, machine):
        super().enter(machine)
        self.blinks_remaining = machine.flags.get('blink_count', 0)
        machine.log.info(f"Starting to blink {self.blinks_remaining} times.")
        
        if self.blinks_remaining <= 0:
            machine.go_to_state('Idle')
            return

        # Start the first blink
        machine.led.value = True
        self.next_toggle_time = time.monotonic() + BLINK_ON_TIME

    def update(self, machine):
        if time.monotonic() >= self.next_toggle_time:
            # Toggle the LED
            machine.led.value = not machine.led.value
            
            if machine.led.value: # Just turned ON (start of a new cycle)
                self.next_toggle_time = time.monotonic() + BLINK_ON_TIME
            else: # Just turned OFF (end of a cycle)
                self.blinks_remaining -= 1
                self.next_toggle_time = time.monotonic() + BLINK_OFF_TIME

            # Check if all blink cycles are complete
            if self.blinks_remaining <= 0:
                machine.log.info("Blinking complete.")
                # Send a SUCCESS response back to the host
                response = Message.create_message(
                    subsystem_name=machine.name,
                    status="SUCCESS",
                    payload={"detail": f"Completed {machine.flags.get('blink_count', 0)} blinks."}
                )
                machine.postman.send(response.serialize())
                
                # Clean up and transition back to Idle
                machine.flags['blink_count'] = 0
                machine.led.value = False
                machine.go_to_state('Idle')

class Error(State):
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