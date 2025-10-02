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
# 1. INSTRUMENT CONFIGURATION
# ============================================================================
SUBSYSTEM_NAME = "COLORIMETER"
SUBSYSTEM_VERSION = "1.1.0" # Incremented version for new features/protocol
SUBSYSTEM_INIT_STATE = "Initialize"
SUBSYSTEM_CONFIG = {
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
    "min_intensity": 1,
    "max_intensity": 10,
}

# ============================================================================
# 2. ASSEMBLY SECTION
# ============================================================================

# REFACTORED: This callback now adheres to the messaging.md protocol.
def send_telemetry(machine):
    """Callback function to generate and send the colorimeter's telemetry."""
    try:
        led_on = machine.sensor.led
        led_current = machine.sensor.led_current

        machine.log.debug(f"Telemetry: LED On={led_on}, Current={led_current}mA")

        telemetry_message = Message.create_message(
            subsystem_name=machine.name,
            status="TELEMETRY",
            payload={
                "metadata": {
                    "data_type": "led_status"
                },
                "data": {
                    "is_on": led_on,
                    "intensity_ma": led_current
                }
            }
        )
        machine.postman.send(telemetry_message.serialize())
    except Exception as e:
        machine.log.error(f"Failed to send telemetry: {e}")

def build_status(machine):
    """Builds the instrument-specific status dictionary for the get_info command."""
    return {
        "is_led_on": machine.sensor.led,
        "gain": machine.sensor.gain,
        "intensity_ma": machine.sensor.led_current
    }

# ============================================================================
# MACHINE ASSEMBLY
# ============================================================================

machine = StateMachine(
    name=SUBSYSTEM_NAME,
    version=SUBSYSTEM_VERSION,
    config=SUBSYSTEM_CONFIG,
    init_state=SUBSYSTEM_INIT_STATE,
    status_callback=build_status
)

postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# --- Add States ---
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_telemetry))
machine.add_state(GenericError())
# NEW: Add the states required for the sequencer-driven 'measure' command
machine.add_state(states.TurnOnLED())
machine.add_state(states.ReadSensor())
machine.add_state(states.TurnOffLED())

# --- Define Command Interface (REFACTORED) ---
register_common_commands(machine)

machine.add_command("read_all", handlers.handle_read_all, {
    "description": "Immediately reads all 10 color channels and returns the values.",
    "args": []
})
machine.add_command("get_settings", handlers.handle_get_settings, {
    "description": "Gets the current sensor settings (gain, LED status, intensity).",
    "args": []
})
machine.add_command("set_settings", handlers.handle_set_settings, {
    "description": "Sets one or more sensor parameters.",
    "args": [
        {"name": "gain", "type": "int", "description": "Sensor gain. See sensor docs for valid values.", "default": None},
        {"name": "led", "type": "bool", "description": "LED on/off state (true/false).", "default": None},
        {"name": "intensity", "type": "int", "description": f"LED current [{SUBSYSTEM_CONFIG['min_intensity']}-{SUBSYSTEM_CONFIG['max_intensity']}] mA.", "default": None}
    ]
})
# NEW: Command to demonstrate the StateSequencer
machine.add_command("measure", handlers.handle_measure, {
    "description": "Performs a full measurement sequence (LED on, read, LED off).",
    "args": []
})

# --- Add machine-wide flags (dynamic variables) ---
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 10.0)