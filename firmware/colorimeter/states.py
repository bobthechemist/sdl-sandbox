# firmware/colorimeter/states.py
# This file defines the unique behaviors (states) for the colorimeter.
# type: ignore
import board
from shared_lib.statemachine import State

# This is the hardware-specific library for the sensor.
# Per your instructions, we assume this is already on the device's /lib folder.
import adafruit_as7341

class Initialize(State):
    """
    Initializes the I2C bus and the AS7341 sensor. This state is custom
    because every instrument has a unique hardware setup procedure. On success,
    it applies default settings from the config and transitions to Idle.
    """
    @property
    def name(self):
        return 'Initialize'

    def enter(self, machine):
        super().enter(machine)
        try:
            # 1. Create the I2C bus object using the board's default SCL/SDA pins.
            i2c = board.I2C()

            # 2. Create the sensor object and attach it to the machine instance
            #    so other states and handlers can access it via `machine.sensor`.
            machine.sensor = adafruit_as7341.AS7341(i2c)
            machine.log.info("AS7341 sensor found and initialized.")

            # 3. Apply default settings from the config dictionary.
            default_gain = machine.config.get("default_gain", 8)
            default_intensity = machine.config.get("default_intensity", 4)

            machine.sensor.gain = default_gain
            machine.sensor.led_current = default_intensity
            machine.sensor.led = False # Ensure LED is off at start

            machine.log.info(f"Default settings applied: Gain={default_gain}, Intensity={default_intensity}mA")

            # 4. Once initialization is successful, transition to the Idle state.
            machine.go_to_state('Idle')

        except Exception as e:
            # If the sensor is not found or another error occurs, we must
            # enter the Error state to halt operation and report the problem.
            machine.flags['error_message'] = f"Failed to initialize AS7341 sensor: {e}"
            machine.log.critical(machine.flags['error_message'])
            machine.go_to_state('Error')

class Collecting(State):
    """
    A placeholder state for future data collection routines (e.g., time series).
    As requested, this state is defined but not currently reachable by any command.
    If it were entered, it would log a message and immediately return to Idle.
    """
    @property
    def name(self):
        return 'Collecting'

    def enter(self, machine):
        super().enter(machine)
        machine.log.warning("Entered placeholder 'Collecting' state. Not implemented.")
        # TODO: Implement data collection logic here in the future.
        # For now, immediately return to a safe state.
        machine.go_to_state('Idle')

    def update(self, machine):
        # Since we transition on enter, update should not be called.
        pass