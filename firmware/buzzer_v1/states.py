# firmware/buzzer_v1/states.py
# type: ignore
import board
import busio
import adafruit_drv2605
from shared_lib.statemachine import State
from firmware.common.common_states import listen_for_instructions

class Initialize(State):
    """
    Initializes the I2C connection and the DRV2605 haptic controller,
    and sets up the default hardware configurations.
    """
    @property
    def name(self): return 'Initialize'

    def enter(self, machine, context=None):
        super().enter(machine, context)
        try:
            machine.hardware = {}
            
            # Initialize I2C Bus
            i2c = busio.I2C(board.SCL, board.SDA)
            machine.hardware['i2c'] = i2c
            
            # Initialize DRV2605L Controller
            drv = adafruit_drv2605.DRV2605(i2c)
            machine.hardware['drv'] = drv
            
            # Setup Operational Parameters
            default_effect = machine.config['operational_parameters']['effect']
            drv.sequence[0] = default_effect
            drv.sequence[1] = 0 # Safety: ensure multi-sequence is terminated
            
            machine.flags['current_effect'] = default_effect
            machine.flags['is_active'] = False
            
            machine.log.info("BUZZER_V1 hardware initialized via I2C.")
            machine.go_to_state('Idle')
            
        except Exception as e:
            machine.log.error(f"Hardware Initialization failed: {e}")
            machine.flags['error_message'] = str(e)
            # If standard Error state is added later, transition there. 
            # Otherwise park in Idle as fallback.
            machine.go_to_state('Idle')

class Buzzing(State):
    """
    Continuous state that actively keeps the motor playing its effect.
    Listens for instruction commands dynamically to allow clean interruption.
    """
    @property
    def name(self): return 'Buzzing'

    def enter(self, machine, context=None):
        super().enter(machine, context)
        machine.flags['is_active'] = True
        machine.hardware['drv'].play()
        machine.log.info("Motor buzzing started.")

    def update(self, machine):
        super().update(machine)
        
        # Crucial: Allow system to process commands (like `motor_off`) 
        # while blocked inside this state.
        listen_for_instructions(machine)
        
        # Poll internal GO register (0x0C) to see if effect has naturally terminated
        # Returns 1 while running, 0 when stopped
        status = machine.hardware['drv']._read_u8(0x0c)
        if status == 0:
            machine.hardware['drv'].play()

    def exit(self, machine):
        super().exit(machine)
        machine.hardware['drv'].stop()
        machine.flags['is_active'] = False
        machine.log.info("Motor buzzing stopped.")