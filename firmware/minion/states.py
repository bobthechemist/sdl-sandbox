# firmware/minion/states.py
# type: ignore
import board
import busio
import time
import adafruit_drv2605
import adafruit_as7341
from shared_lib.statemachine import State
from shared_lib.messages import Message

# ============================================================================
# GLOBAL BACKGROUND CALLBACK
# ============================================================================

def run_minion_background(machine):
    """
    Global background loop executed every update cycle.
    Handles background communication and motor looping independently of states.
    """
    # 1. Listen for serial commands globally
    # Removes need for states to manually implement instruction handlers
    from firmware.common.common_states import listen_for_instructions
    listen_for_instructions(machine)

    # 2. Maintain haptic motor playback if is_active is enabled
    if machine.flags.get('is_active', False):
        try:
            # Poll internal GO register (0x0C) to verify loop status
            status = machine.hardware['drv']._read_u8(0x0c)
            if status == 0:
                machine.hardware['drv'].play()
        except Exception as e:
            machine.log.error(f"Background DRV2605 check failed: {e}")

# ============================================================================
# PRIMARY SYSTEM STATES
# ============================================================================

class Initialize(State):
    """
    Initializes the shared I2C bus and sets up default parameters
    for both the AS7341 spectral sensor and the DRV2605 haptic controller.
    """
    @property
    def name(self): return 'Initialize'

    def enter(self, machine, context=None):
        super().enter(machine, context)
        try:
            machine.hardware = {}
            
            # 1. Initialize Shared I2C Bus
            i2c = busio.I2C(board.SCL, board.SDA)
            machine.hardware['i2c'] = i2c
            
            # 2. Initialize DRV2605 Controller
            drv = adafruit_drv2605.DRV2605(i2c)
            machine.hardware['drv'] = drv
            
            default_effect = machine.config['operational_parameters']['effect']
            drv.sequence[0] = adafruit_drv2605.Effect(default_effect)
            drv.sequence[1] = adafruit_drv2605.Effect(0) # Safety: ensure multi-sequence is terminated
            
            machine.flags['current_effect'] = default_effect
            machine.flags['is_active'] = False
            machine.log.info("DRV2605 motor hardware initialized via shared I2C.")
            
            # 3. Initialize AS7341 Sensor
            machine.sensor = adafruit_as7341.AS7341(i2c)
            machine.log.info("AS7341 sensor found and initialized via shared I2C.")

            default_gain_val = machine.config.get("default_gain", 8)
            default_intensity = machine.config.get("default_intensity", 4)
            
            from .handlers import VALID_GAINS
            machine.sensor.gain = VALID_GAINS.index(default_gain_val)
            machine.sensor.led_current = default_intensity
            machine.sensor.led = False
            machine.log.info(f"Colorimeter default settings: Gain={default_gain_val}x, Intensity={default_intensity}mA")

            machine.go_to_state('Idle')
            
        except Exception as e:
            machine.flags['error_message'] = f"Hardware Initialization failed: {e}"
            machine.log.critical(machine.flags['error_message'])
            machine.go_to_state('Error')

class Buzzing(State):
    """
    Continuous state that monitors motor playback activity.
    The primary looping responsibility is delegated to the background callback.
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
        # Background loop handles periodic play triggers dynamically

    def exit(self, machine):
        super().exit(machine)
        # Transition out of state without cutting hardware power if motor is active.
        # Allows background task to keep stirring during sequencer tasks.
        if not machine.flags.get('is_active', False):
            machine.hardware['drv'].stop()
            machine.log.info("Motor buzzing stopped.")
        else:
            machine.log.info("Buzzing state exited, motor continues spinning in background.")

# ============================================================================
# STATES FOR THE 'measure' COMMAND SEQUENCE
# ============================================================================

class TurnOnLED(State):
    """Sequencer State: Turns the LED on and waits briefly for it to stabilize."""
    @property
    def name(self): return 'TurnOnLED'

    def enter(self, machine, context=None):
        super().enter(machine, context)
        machine.sensor.led = True
        time.sleep(0.2)
        self.task_complete = True

    def update(self, machine):
        super().update(machine)

class ReadSensor(State):
    """Sequencer State: Reads the sensor and stores the result in the sequencer's context."""
    @property
    def name(self): return 'ReadSensor'

    def enter(self, machine, context=None):
        super().enter(machine, context)
        machine.sequencer.context['raw_readings'] = machine.sensor.all_channels
        machine.log.info("Sensor readings acquired.")
        self.task_complete = True

    def update(self, machine):
        super().update(machine)

class TurnOffLED(State):
    """Sequencer State: Turns LED off, formats data, and sends the final response."""
    @property
    def name(self): return 'TurnOffLED'

    def enter(self, machine, context=None):
        super().enter(machine, context)
        machine.sensor.led = False
        
        readings_tuple = machine.sequencer.context.get('raw_readings')
        
        if readings_tuple:
            from .handlers import CHANNEL_NAMES
            readings_dict = dict(zip(CHANNEL_NAMES, readings_tuple))
            response = Message.create_message(
                subsystem_name=machine.name,
                status="DATA_RESPONSE",
                payload={
                    "metadata": { "data_type": "color_spectrum", "units": "counts" },
                    "data": readings_dict
                }
            )
            machine.postman.send(response.serialize())
        else:
            from shared_lib.messages import send_problem
            send_problem(machine, "Measurement failed: could not retrieve sensor data from context.")

        self.task_complete = True

    def update(self, machine):
        super().update(machine)