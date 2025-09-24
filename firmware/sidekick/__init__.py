# firmware/sidekick/__init__.py
# type: ignore
import board
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from our common firmware library
from firmware.common.common_states import GenericErrorWithButton, GenericIdle
from firmware.common.command_library import register_common_commands

# Import the device-specific parts we will write
from . import states
from . import handlers

# ============================================================================
# 1. INSTRUMENT CONFIGURATION
# ============================================================================
SUBSYSTEM_NAME = "SIDEKICK"
SUBSYSTEM_VERSION = "1.0.0"
SUBSYSTEM_INIT_STATE = "Initialize"
SUBSYSTEM_CONFIG = {
    "pins": {
        # M1 is the top motor, controls A1 (arm with arrow)
        "motor1_step": board.GP1, "motor1_dir": board.GP0, "motor1_enable": board.GP7,
        "motor2_step": board.GP10, "motor2_dir": board.GP9, "motor2_enable": board.GP16,
        "motor1_m0": board.GP6, "motor1_m1": board.GP5,
        "motor2_m0": board.GP15, "motor2_m1": board.GP14,
        "endstop_m1": board.GP18, "endstop_m2": board.GP19,
        "user_button": board.GP20,
        "pump1": board.GP27, "pump2": board.GP26, "pump3": board.GP22, "pump4": board.GP21,
    },
    "motor_settings": {
        "step_angle_degrees": 0.9, "microsteps": 8, "max_speed_sps": 200,
    },
    "pump_timings": {
        "aspirate_time": 0.1, "dispense_time": 0.1, "increment_ul": 10.0,
    },
    "kinematics": {
        "L1": 7.0, "L2": 3.0, "L3": 10.0, "Ln": 0.5,
    },
    "safe_limits": {
        # These are placeholder values and need to be updated.
        "m1_max_steps": 1600, "m2_max_steps": 1600,
    },
    "homing_settings": {
        # The number of steps for M1 to back off endstop 2.
        "joint_backoff_steps": 20,
        # Set the position of the arm after homing
        "park_move_x": 10.0, # cm
        "park_move_y": 5.0, # cm
    },
        "operational_limits_degrees": {
        "m1_min": 0.0,
        "m1_max": 160.0,
        "m2_min": 90.0,
        "m2_max": 180.0
    },
    "pump_offsets": {
        "p1": {"dx": 0.5, "dy": 0.0}, "p2": {"dx": 0.0, "dy": 0.5},
        "p3": {"dx": -0.5, "dy": 0.0}, "p4": {"dx": 0.0, "dy": -0.5},
    }
}

# ============================================================================
# 2. ASSEMBLY SECTION
# ============================================================================

# This callback defines the device's specific telemetry data.
def send_telemetry(machine):
    """Generates and sends telemetry message."""
    telemetry_message = Message.create_message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={
            "m1_steps": machine.flags.get('current_m1_steps'),
            "m2_steps": machine.flags.get('current_m2_steps')
        }
    )
    machine.postman.send(telemetry_message.serialize())

def build_status(machine):
    """
    This function is called by the generic get_info command.
    It builds the instrument-specific status dictionary in real-time.
    """
    return {
        # Public Key:  Reads from the internal flag at the moment of the request.
        "homed": machine.flags.get('is_homed', False)
        # Add other public-facing status values here in the future
        # "gripper_state": machine.flags.get('gripper_is_open', False)
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
machine.add_state(states.Homing())
machine.add_state(states.Moving())
machine.add_state(states.Dispensing())
machine.add_state(GenericErrorWithButton(reset_pin=machine.config['pins']['user_button'], reset_state_name='Idle'))

# --- Define Command Interface ---
register_common_commands(machine) # Adds common commands
machine.add_command("home", handlers.handle_home, {
    "description": "Finds motor zero via endstops, then moves to a safe parking spot.",
    "args": []
})
machine.add_command("move_to", handlers.handle_move_to, {
    "description": "Moves the arm's center point to an absolute (x, y) coordinate.",
    "args": [
        {"name": "x", "type": "float", "description": "Target x-coordinate (cm)"},
        {"name": "y", "type": "float", "description": "Target y-coordinate (cm)"}
    ]
})
machine.add_command("move_rel", handlers.handle_move_rel, {
    "description": "Moves the arm relative to its current position by (dx, dy).",
    "args": [
        {"name": "dx", "type": "float", "description": "Relative move in x-axis (cm)"},
        {"name": "dy", "type": "float", "description": "Relative move in y-axis (cm)"}
    ]
})
machine.add_command("dispense", handlers.handle_dispense, {
    "description": "Dispenses from a pump at the current location.",
    "args": [
        {"name": "pump", "type": "str", "description": "Pump to use (e.g., 'p1')"},
        {"name": "vol", "type": "float", "description": "Volume to dispense (uL)", "default": 10.0}
    ]
})
machine.add_command("dispense_at", handlers.handle_dispense_at, {
    "description": "Moves a pump to an absolute (x, y) coordinate and then dispenses.",
    "args": [
        {"name": "pump", "type": "str", "description": "Pump to use (e.g., 'p1')"},
        {"name": "vol", "type": "float", "description": "Volume to dispense (uL)", "default": 10.0},
        {"name": "x", "type": "float", "description": "Target x-coordinate (cm)"},
        {"name": "y", "type": "float", "description": "Target y-coordinate (cm)"}
    ]
})
machine.add_command("steps", handlers.handle_steps, {
    "description": "Moves motors by a relative number of steps. FOR TESTING ONLY.",
    "args": [
        {"name": "m1", "type": "int", "description": "Relative steps for motor 1"},
        {"name": "m2", "type": "int", "description": "Relative steps for motor 2"}
    ]
})
machine.add_command("angles", handlers.handle_angles, {
    "description": "Moves motors to absolute angles (theta1, theta2) within safe limits.",
    "args": [
        {"name": "theta1", "type": "float", "description": "Absolute angle for motor 1 (degrees)"},
        {"name": "theta2", "type": "float", "description": "Absolute angle for motor 2 (degrees)"}
    ]
})

# --- Add Dynamic Flags
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 60.0)
# --- Public flags are available via get_info ---
machine.add_flag('is_homed', False)
# --- Positioning flags ---
machine.add_flag('current_m1_steps', 0)
machine.add_flag('current_m2_steps', 0)
machine.add_flag('target_m1_steps', 0)
machine.add_flag('target_m2_steps', 0)
# --- Dispensing flags ---
machine.add_flag('dispense_pump', None)
machine.add_flag('dispense_cycles', 0)
machine.add_flag('on_move_complete', None) # For the state sequencer