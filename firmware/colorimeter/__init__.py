# firmware/colorimeter/__init__.py
# type: ignore
import board
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from the common firmware library
from firmware.common.common_states import GenericIdle, GenericError
from firmware.common.command_library import register_common_commands

# Import the device-specific parts we just defined
from . import states
from . import handlers

# ============================================================================
# COLORIMETER INSTRUMENT CONFIGURATION
# ============================================================================
# This dictionary holds all static configuration for the instrument.
# It separates hardware definitions from the logic in states and handlers.
COLORIMETER_CONFIG = {
    "pins": {
        # The AS7341 sensor uses the board's default I2C pins.
        # They are listed here for clarity but are not directly used in the
        # code, as `board.I2C()` finds them automatically.
        "SCL": board.SCL,
        "SDA": board.SDA
    },
    # Default gain setting for the sensor on initialization.
    "default_gain": 8,
    # Default current for the onboard LED source (mA).
    "default_intensity": 4,
}

# ============================================================================
# TELEMETRY CALLBACK
# ============================================================================
# This function is passed to the GenericIdle state. It defines what data
# this specific instrument should send back to the host periodically.
def send_colorimeter_telemetry(machine):
    """Callback function to generate and send the colorimeter's telemetry."""
    try:
        # Per your request, telemetry includes both LED status and current.
        led_on = machine.sensor.led
        led_current = machine.sensor.led_current

        machine.log.debug(f"Telemetry: LED On={led_on}, Current={led_current}mA")

        telemetry_message = Message.create_message(
            subsystem_name=machine.name,
            status="TELEMETRY",
            payload={
                "led_is_on": led_on,
                "led_intensity_ma": led_current
            }
        )
        machine.postman.send(telemetry_message.serialize())
    except Exception as e:
        machine.log.error(f"Failed to send telemetry: {e}")

# ============================================================================
# MACHINE ASSEMBLY
# ============================================================================

# 1. Create the state machine instance
machine = StateMachine(init_state='Initialize', name='COLORIMETER')

# 2. Attach the configuration and communication channel (Postman)
machine.config = COLORIMETER_CONFIG
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the states the machine can be in
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_colorimeter_telemetry))
machine.add_state(states.Collecting())  # Placeholder state, not currently reachable
machine.add_state(GenericError())

# 4. Define the machine's command interface by mapping command strings
#    to their handler functions and providing documentation.
register_common_commands(machine)  # Adds 'ping' and 'help'

machine.add_command("read", handlers.handle_read, {
    "description": "Returns the reading for a single specified color channel.",
    "args": ["channel: str (e.g., 'violet', 'blue', 'nir')"]
})
machine.add_command("read_all", handlers.handle_read_all, {
    "description": "Returns an object containing readings from all color channels.",
    "args": []
})
machine.add_command("read_gain", handlers.handle_read_gain, {
    "description": "Reads the current sensor gain setting.",
    "args": []
})
machine.add_command("set_gain", handlers.handle_set_gain, {
    "description": "Sets the sensor gain. Must be one of the allowed values.",
    "args": ["gain: float (0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512)"]
})
machine.add_command("led", handlers.handle_led, {
    "description": "Turns the onboard illumination LED on or off.",
    "args": ["state: bool (true/false)"]
})
machine.add_command("led_intensity", handlers.handle_led_intensity, {
    "description": "Adjusts the LED illumination intensity.",
    "args": ["current: int (1-10)"]
})

# 5. Add machine-wide flags (dynamic variables)
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 60.0)  # Send telemetry every 10 seconds