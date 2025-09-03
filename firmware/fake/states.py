# firmware/fake/states.py
# type: ignore
import time
import board
import digitalio
import analogio
from shared_lib.statemachine import State
from shared_lib.messages import Message

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

class Blinking(State):
    """
    Handles the non-blocking logic for blinking the LED a set number of times.
    """
    @property
    def name(self):
        return 'Blinking'

    def enter(self, machine):
        """
        Called once when entering the Blinking state. Sets up the blink count
        and initializes the timer for the first toggle.
        """
        super().enter(machine)
        self.blinks_remaining = machine.flags.get('blink_count', 0)
        machine.log.info(f"Starting to blink {self.blinks_remaining} times.")
        
        # Handle the case where we are asked to blink 0 or fewer times.
        if self.blinks_remaining <= 0:
            machine.led.value = False # Ensure LED is off
            machine.go_to_state('Idle')
            return

        # --- THE FIX IS HERE ---
        # Start the first blink immediately and set the timer for the next toggle.
        machine.led.value = True
        # Initialize the 'next_toggle_time' attribute on self.
        self.next_toggle_time = time.monotonic() + machine.flags['blink_on_time'] # BLINK_ON_TIME

    def update(self, machine):
        """
        Called repeatedly. Checks the timer and toggles the LED or returns
        to Idle when complete.
        """
        # This check will now work correctly.
        if time.monotonic() >= self.next_toggle_time:
            # Toggle the LED
            machine.led.value = not machine.led.value
            
            if machine.led.value: # Just turned ON (start of a new cycle)
                self.next_toggle_time = time.monotonic() + machine.flags['blink_on_time'] # BLINK_ON_TIME
            else: # Just turned OFF (end of a cycle)
                self.blinks_remaining -= 1
                self.next_toggle_time = time.monotonic() + machine.flags['blink_off_time'] # BLINK_OFF_TIME

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