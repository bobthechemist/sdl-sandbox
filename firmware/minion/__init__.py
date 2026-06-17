# firmware/minion/__init__.py
# type: ignore
import board
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from common firmware library
from firmware.common.common_states import GenericIdle, GenericError
from firmware.common.command_library import register_common_commands

# Import specific components
from . import states
from . import handlers

# ============================================================================
# 1. INSTRUMENT CONFIGURATION
# ============================================================================
SUBSYSTEM_NAME = "MINION"
SUBSYSTEM_VERSION = "1.0.0"
SUBSYSTEM_INIT_STATE = "Initialize"
SUBSYSTEM_CONFIG = {
    "pins": {
        "SCL": board.SCL,
        "SDA": board.SDA
    },
    "operational_parameters": {
        "effect": 64
    },
    "safe_limits": {
        "max_effect": 123,
        "min_effect": 0
    },
    "default_gain": 8,
    "default_intensity": 4,
    "min_intensity": 1,
    "max_intensity": 10,
    "ai_guidance": (
        "This motor is connected to a 96-well plate and is used to sonically stir the solutions in the wells. "
        "1. Use 'motor_on' to start sonic stirring indefinitely. "
        "2. Use 'motor_off' to stop the stirring. "
        "3. Use 'set_effect' to change the stirring intensity/pattern (0 to 123). The motor must be OFF to change the effect. "
        "Additionally, the colorimeter is mounted on the Sidekick arm. You MUST ensure the Sidekick has "
        "centered the arm over the target well (using to_well with no pump argument) "
        "before calling the 'measure' command."
    )
}

# ============================================================================
# 2. ASSEMBLY SECTION
# ============================================================================

def send_telemetry(machine):
    """Generates and sends telemetry message containing device indicators."""
    try:
        is_active = machine.flags.get('is_active', False)
        current_effect = machine.flags.get('current_effect', SUBSYSTEM_CONFIG['operational_parameters']['effect'])
        led_on = machine.sensor.led
        led_current = machine.sensor.led_current

        telemetry_message = Message(
            subsystem_name=machine.name,
            status="TELEMETRY",
            payload={
                "data": {
                    "motor_is_active": is_active,
                    "current_effect": current_effect,
                    "led_is_on": led_on,
                    "intensity_ma": led_current
                }
            }
        )
        machine.postman.send(telemetry_message.serialize())
    except Exception as e:
        machine.log.error(f"Failed to generate telemetry: {e}")

def build_status(machine):
    """
    Builds the status dictionary for the get_info command.
    """
    return {
        "motor_is_active": machine.flags.get('is_active', False),
        "current_effect": machine.flags.get('current_effect', SUBSYSTEM_CONFIG['operational_parameters']['effect']),
        "is_led_on": machine.sensor.led,
        "gain": machine.sensor.gain,
        "intensity_ma": machine.sensor.led_current
    }

# --- Machine Assembly ---
machine = StateMachine(
    name=SUBSYSTEM_NAME,
    version=SUBSYSTEM_VERSION,
    config=SUBSYSTEM_CONFIG,
    init_state=SUBSYSTEM_INIT_STATE,
    status_callback=build_status,
    background_callback=states.run_minion_background  # Standardized Option A Callback Hook
)

# --- Attach Communication Channel ---
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# --- Add States ---
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_telemetry))
machine.add_state(GenericError())
machine.add_state(states.Buzzing())
machine.add_state(states.TurnOnLED())
machine.add_state(states.ReadSensor())
machine.add_state(states.TurnOffLED())

# --- Define Command Interface ---
register_common_commands(machine)

machine.add_command("motor_on", handlers.handle_motor_on, {
    "description": "Turns on the buzzing motor to sonically stir the solution.",
    "args": [],
    "ai_enabled": True,
    "effects": ["motor begins buzzing continuously"]
})

machine.add_command("motor_off", handlers.handle_motor_off, {
    "description": "Turns off the buzzing motor.",
    "args": [],
    "ai_enabled": True,
    "effects": ["motor stops buzzing"]
})

machine.add_command("set_effect", handlers.handle_set_effect, {
    "description": "Changes the effect value for the motor buzzing (0 to 123).",
    "args": [
        {"name": "effect", "type": "int", "description": "Effect ID to apply.", "default": 64}
    ],
    "ai_enabled": True,
    "usage_notes": "The motor must be off before changing the effect."
})

machine.add_command("read_all", handlers.handle_read_all, {
    "description": "Immediately reads all 10 color channels and returns the values.",
    "args": [],
    "ai_enabled": True
})

machine.add_command("get_settings", handlers.handle_get_settings, {
    "description": "Gets the current sensor settings (gain, LED status, intensity).",
    "args": [],
    "ai_enabled": True
})

machine.add_command("set_settings", handlers.handle_set_settings, {
    "description": "Sets one or more sensor parameters.",
    "args": [
        {"name": "gain", "type": "int", "description": "Sensor gain [0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512].", "default": None},
        {"name": "led", "type": "bool", "description": "LED on/off state (true/false).", "default": None},
        {"name": "intensity", "type": "int", "description": f"LED current [{SUBSYSTEM_CONFIG['min_intensity']}-{SUBSYSTEM_CONFIG['max_intensity']}] mA.", "default": None}
    ],
    "ai_enabled": True
})

machine.add_command("measure", handlers.handle_measure, {
    "description": "Performs a full measurement sequence (LED on, read, LED off).",
    "args": [],
    "ai_enabled": True,
    "effects": ["a spectral measurement is taken at the current arm position and the data is returned"],
    "usage_notes": "This command requires the arm to be centered over the target well. Ensure a 'sidekick.to_well' command (with no 'pump' argument) is called first."
})

# Override common commands to ensure AI planner does not waste tokens on them
machine.supported_commands['help']['ai_enabled'] = False
machine.supported_commands['ping']['ai_enabled'] = False
machine.supported_commands['set_time']['ai_enabled'] = False
machine.supported_commands['get_info']['ai_enabled'] = False

# --- Add Dynamic Flags ---
machine.add_flag('is_active', False)
machine.add_flag('current_effect', SUBSYSTEM_CONFIG['operational_parameters']['effect'])
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 15.0)