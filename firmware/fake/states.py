# type: ignore
import time
import board
import digitalio
import analogio
from shared_lib.statemachine import State
from shared_lib.messages import Message

# Constants for the state machine
ANALOG_READ_INTERVAL = 5.0  # seconds
BLINK_ON_TIME = 0.25        # seconds
BLINK_OFF_TIME = 0.25       # seconds

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
        super().enter(machine)
        # Set a timer for the next analog data transmission
        self.next_analog_read_time = time.monotonic() + ANALOG_READ_INTERVAL
        machine.log.info("Entering Idle state. Listening for commands.")

    def update(self, machine):
        # 1. Check for incoming commands from the host
        raw_message = machine.postman.receive()
        if raw_message:
            try:
                message = Message.from_json(raw_message)
                machine.log.info(f"Received message: {message.to_dict()}")

                if message.status == "INSTRUCTION":
                    payload = message.payload
                    if isinstance(payload, dict) and payload.get("func") == "blink":
                        # Got a blink command; parse args and switch to the Blinking state
                        try:
                            count = int(payload.get("args", [1])[0])
                        except (ValueError, IndexError):
                            count = 1  # Default to 1 blink
                        
                        machine.flags['blink_count'] = count
                        machine.log.info(f"Blink request received for {count} times.")
                        machine.go_to_state('Blinking')
                        return # Exit update early since we changed state
            except Exception as e:
                machine.log.error(f"Could not process message: '{raw_message}'. Error: {e}")

        # 2. Send periodic analog data (HEARTBEAT)
        if time.monotonic() >= self.next_analog_read_time:
            analog_value = machine.analog_in.value
            machine.log.info(f"Reading analog value: {analog_value}")
            
            heartbeat_message = Message.create_message(
                subsystem_name=machine.name,
                status="HEARTBEAT",
                payload={"analog_value": analog_value}
            )
            
            machine.postman.send(heartbeat_message.serialize())
            self.next_analog_read_time = time.monotonic() + ANALOG_READ_INTERVAL

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