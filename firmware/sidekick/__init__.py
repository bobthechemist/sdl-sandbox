# firmware/sidekick/__init__.py
# type: ignore
import board
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from our common firmware library
from firmware.common.common_states import GenericErrorWithButton
from firmware.common.command_library import register_common_commands

# Import the device-specific parts we will write
from . import states
from . import handlers


# ============================================================================
# SIDEKICK INSTRUMENT CONFIGURATION
# ============================================================================
SIDEKICK_CONFIG = {
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
        "step_angle_degrees": 0.9, "microsteps": 8, "max_speed_sps": 150,
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

# This callback defines the device's specific telemetry data.
def send_sidekick_telemetry(machine):
    # This assumes a function exists to convert motor steps to Cartesian coords.
    # For now, we'll send the raw steps.
    # pos_xy = kf.forward_kinematics(machine.flags['current_m1_steps'], ...)
    telemetry_message = Message.create_message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={
            "m1_steps": machine.flags.get('current_m1_steps'),
            "m2_steps": machine.flags.get('current_m2_steps')
            # "x": pos_xy['x'], "y": pos_xy['y'] # This would be the ideal implementation
        }
    )
    machine.postman.send(telemetry_message.serialize())

# 1. Create the state machine instance
machine = StateMachine(init_state='Initialize', name='SIDEKICK')

# 2. Attach the configuration and Postman
machine.config = SIDEKICK_CONFIG
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman
reset_pin = machine.config['pins']['user_button']

# 3. Add all the states the machine can be in
machine.add_state(states.Initialize())
# AI Generated a custom Idle state, so we'll use that
#machine.add_state(states.Idle(telemetry_callback=send_sidekick_telemetry))
machine.add_state(states.Idle())
machine.add_state(states.Homing())
machine.add_state(states.Moving())
machine.add_state(states.Dispensing())
machine.add_state(GenericErrorWithButton(reset_pin=reset_pin, reset_state_name='Idle'))

# 4. Define the machine's command interface
register_common_commands(machine) # Adds 'ping' and 'help'
machine.add_command("home", handlers.handle_home, {
    "description": "Finds motor zero via endstops, then moves to a safe parking spot.",
    "args": []
})
machine.add_command("move_to", handlers.handle_move_to, {
    "description": "Moves the arm's center point to an absolute (x, y) coordinate.",
    "args": ["x: float (cm)", "y: float (cm)"]
})
machine.add_command("move_rel", handlers.handle_move_rel, {
    "description": "Moves the arm relative to its current position by (dx, dy).",
    "args": ["dx: float", "dy: float"]
})
machine.add_command("dispense", handlers.handle_dispense, {
    "description": "Dispenses from a pump at the current location (includes offset move).",
    "args": ["pump: str (e.g., 'p1')", "vol: float"]
})
machine.add_command("dispense_at", handlers.handle_dispense_at, {
    "description": "Moves a pump to an absolute (x, y) coordinate and then dispenses.",
    "args": ["pump: str", "vol: float", "x: float", "y: float"]
})
machine.add_command("steps", handlers.handle_steps, {
    "description": "Moves motors by a relative number of steps. FOR TESTING ONLY.",
    "args": ["m1: int", "m2: int"]
})
machine.add_command("angles", handlers.handle_angles, {
    "description": "Moves motors to absolute angles (theta1, theta2) within safe limits.",
    "args": ["theta1: float", "theta2: float"]
})

# 5. Add dynamic flags (values that will change during operation)
machine.add_flag('is_homed', False)
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 2.0)
machine.add_flag('current_m1_steps', 0)
machine.add_flag('current_m2_steps', 0)
machine.add_flag('target_m1_steps', 0)
machine.add_flag('target_m2_steps', 0)
machine.add_flag('dispense_pump', None)
machine.add_flag('dispense_cycles', 0)
machine.add_flag('on_move_complete', None) # For the state sequencer