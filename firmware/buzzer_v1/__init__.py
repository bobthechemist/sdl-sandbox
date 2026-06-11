# firmware/buzzer_v1/__init__.py
# type: ignore
import board
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from common firmware library
from firmware.common.common_states import GenericIdle
from firmware.common.command_library import register_common_commands

# Import specific components
from . import states
from . import handlers

# ============================================================================
# 1. INSTRUMENT CONFIGURATION
# ============================================================================
SUBSYSTEM_NAME = "BUZZER_V1"
SUBSYSTEM_VERSION = "1.0.0"
SUBSYSTEM_INIT_STATE = "Initialize"
SUBSYSTEM_CONFIG = {
    "operational_parameters": {
        "effect": 64
    },
    "safe_limits": {
        "max_effect": 123,
        "min_effect": 0
    },
    "ai_guidance": (
        "This motor is connected to a 96-well plate and is used to sonically stir the solutions in the wells. "
        "1. Use 'motor_on' to start sonic stirring indefinitely. "
        "2. Use 'motor_off' to stop the stirring. "
        "3. Use 'set_effect' to change the stirring intensity/pattern (0 to 123). The motor must be OFF to change the effect."
    )
}

# ============================================================================
# 2. ASSEMBLY SECTION
# ============================================================================

def send_telemetry(machine):
    """Generates and sends telemetry message containing the motor status."""
    telemetry_message = Message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={
            "data": {
                "is_active": machine.flags.get('is_active', False),
                "current_effect": machine.flags.get('current_effect', SUBSYSTEM_CONFIG['operational_parameters']['effect'])
            }
        }
    )
    machine.postman.send(telemetry_message.serialize())

def build_status(machine):
    """
    Builds the comprehensive status dictionary for the get_info command.
    """
    return {
        "is_active": machine.flags.get('is_active', False),
        "current_effect": machine.flags.get('current_effect', SUBSYSTEM_CONFIG['operational_parameters']['effect'])
    }

# --- Machine Assembly ---
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
machine.add_state(states.Buzzing())

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

# Override common commands to ensure AI planner does not waste tokens on them
machine.supported_commands['help']['ai_enabled'] = False
machine.supported_commands['ping']['ai_enabled'] = False
machine.supported_commands['set_time']['ai_enabled'] = False
machine.supported_commands['get_info']['ai_enabled'] = False

# --- Add Dynamic Flags ---
machine.add_flag('is_active', False)
machine.add_flag('current_effect', SUBSYSTEM_CONFIG['operational_parameters']['effect'])
machine.add_flag('telemetry_interval', 10.0) # Used by GenericIdle