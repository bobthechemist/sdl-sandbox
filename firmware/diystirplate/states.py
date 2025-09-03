# firmware/diystirplate/states.py
from shared_lib.statemachine import State
from time import monotonic
import board
import digitalio
from firmware.common.common_states import listen_for_instructions

class Initialize(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Initialize'

    def enter(self, machine):
        # Setup hardware
        super().enter(machine)
        try:
            machine.tachometer_pin = board.A0
            machine.pwm = digitalio.DigitalInOut(board.D10)
            machine.pwm.direction = digitalio.Direction.OUTPUT
            machine.duty_cycle = 0
            machine.period = 1
            machine.start = True
            machine.log.debug(f"{machine.name} has been Initialized")
            machine.go_to_state('Idle')
        except Exception as e:
            machine.flags['error_message'] = str(e)
            machine.log.critical(f"Initialization of {machine.name} failed: {e}")
            machine.go_to_state('Error')

class Stirring(State):
    @property
    def name(self):
        return 'Stirring'

    def enter(self, machine):
        """Called once when we start stirring."""
        super().enter(machine)
        machine.log.info(f"Entering Stirring state with duty cycle {machine.duty_cycle}")
        
        # Initialize the PWM logic
        machine.pwm.value = True
        self._toggle_time = monotonic() + (machine.duty_cycle * machine.period)

    def update(self, machine):
        """Called on every loop to run the motor AND listen for commands."""
        super().update(machine)

        # 1. ALWAYS listen for commands. This allows an 'off' command to be received.
        listen_for_instructions(machine)

        # 2. Perform the non-blocking PWM work.
        if monotonic() >= self._toggle_time:
            if machine.pwm.value: # Currently HIGH, switch to LOW
                machine.pwm.value = False
                on_time = (1 - machine.duty_cycle) * machine.period
                self._toggle_time = monotonic() + on_time
            else: # Currently LOW, switch to HIGH
                machine.pwm.value = True
                off_time = machine.duty_cycle * machine.period
                self._toggle_time = monotonic() + off_time 
