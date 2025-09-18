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
SUBSYSTEM_VERSION = "1.0.0"
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
}

# ============================================================================
# 2. ASSEMBLY SECTION
# ============================================================================

# This callback defines the device's specific telemetry data.
def send_telemetry(machine):
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
                "data":{
                    "led_is_on": led_on,
                    "led_intensity_ma": led_current
                }
            }
        )
        machine.postman.send(telemetry_message.serialize())
    except Exception as e:
        machine.log.error(f"Failed to send telemetry: {e}")

def build_status(machine):
    """
    This function is called by the generic get_info command.
    It builds the instrument-specific status dictionary in real-time.
    """
    return {
        # Public Key:  Reads from the internal flag at the moment of the request.
        "is_led_on": machine.sensor.led
        # Add other public-facing status values here in the future
        # "gripper_state": machine.flags.get('gripper_is_open', False)
    }

# ============================================================================
# MACHINE ASSEMBLY
# ============================================================================

# 1. Create the state machine instance
machine = StateMachine(
    name=SUBSYSTEM_NAME,
    version=SUBSYSTEM_VERSION,
    config=SUBSYSTEM_CONFIG,
    init_state=SUBSYSTEM_INIT_STATE,
    status_callback=build_status
)

# --- Attach Communication Channel ---
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# --- Add States ---
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_telemetry))
machine.add_state(states.Collecting())  # Placeholder state, not currently reachable
machine.add_state(GenericError())

# --- Define Command Interface ---
register_common_commands(machine)  # Adds 'ping' and 'help'

machine.add_command("read", handlers.handle_read, {
    "description": "Returns an object containing readings from all color channels.",
    "args": []
})
machine.add_command("get", handlers.handle_get, {
    "description": "gets the current parameter dictionary",
    "args": []
})
machine.add_command("set", handlers.handle_set, {
    "description": "Sets parameters (LED on/off, gain, LED intensity)",
    "args": ["gain: float", "led: boolean", "intensity: inteter [1-10]"]
})


# 5. Add machine-wide flags (dynamic variables)
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 60.0)  # Send telemetry every 10 seconds
