# firmware/sidekick/handlers.py
# type: ignore
from shared_lib.messages import Message, send_problem, send_success
from . import kinematics
import math
from shared_lib.error_handling import try_wrapper

def get_current_position_steps(machine):
    """Returns the current position as a tuple of motor steps: (m1, m2)."""
    return (
        machine.flags.get('current_m1_steps', 0),
        machine.flags.get('current_m2_steps', 0)
    )

def get_current_position_degrees(machine):
    """
    Converts current motor steps to degrees.
    Returns: (theta1, theta2)
    """
    m1_steps, m2_steps = _get_current_position_steps(machine)
    return kinematics.steps_to_degrees(machine, m1_steps, m2_steps)

def get_current_position_cartesian(machine):
    """
    Calculates the current Cartesian position of the arm.
    Returns: (x, y)
    """
    theta1, theta2 = _get_current_position_degrees(machine)
    return kinematics.forward_kinematics(machine, theta1, theta2)

def check_homed(machine):
    """Guard condition to ensure the device is homed."""
    if not machine.flags.get('is_homed', False):
        send_problem(machine, "Device must be homed before this operation.")
        return False
    return True

def degrees_to_steps(machine, theta1, theta2):
    """Converts motor angles in degrees to absolute step counts."""
    cfg = machine.config['motor_settings']
    steps_per_rev = (360 / cfg['step_angle_degrees']) * cfg['microsteps']
    
    m1_steps = int((theta1 / 360) * steps_per_rev)
    m2_steps = int((theta2 / 360) * steps_per_rev)
    
    return m1_steps, m2_steps

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

def handle_angles(machine, payload):
    """
    Moves the motors to a specified angular position (theta1, theta2)
    after validating that the target is within safe operational limits.
    """

    send_problem(machine, "Function not implemented")
    return
    
def handle_home(machine, payload):
    machine.log.info("Home command received.")
    machine.go_to_state('Homing')

def handle_move_to(machine, payload):
    """
    Handles the high-level 'move_to' command. It uses inverse kinematics
    to convert Cartesian coordinates into motor steps.
    """
    # 1. Guard Condition: Check if homed
    if not check_homed(machine):
        return

    # 2. Extract and Validate Input Arguments
    args = payload.get("args", {})

    target_x = args.get("x")
    target_y = args.get("y")

    if target_x is None or target_y is None:
        send_problem(machine, "Missing 'x' or 'y' in command arguments.")
        return

    try:
        target_x = float(target_x)
        target_y = float(target_y)
    except ValueError:
        send_problem(machine, "Invalid coordinate format; 'x' and 'y' must be numbers.")
        return

    # 3. Perform Inverse Kinematics
    machine.log.info(f"IK request for (x={target_x}, y={target_y})...")
    target_angles = kinematics.inverse_kinematics(machine, target_x, target_y)

    # 4. Check for IK Failure
    if target_angles is None:
        # The IK function already logged the specific error.
        send_problem(machine, "Inverse kinematics failed. Target may be unreachable or out of safe limits.")
        return
    
    theta1, theta2 = target_angles

    # 5. Convert Validated Angles to Steps
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)
    machine.log.info(f"IK success. Target: ({theta1:.2f}, {theta2:.2f}) degrees -> ({target_m1_steps}, {target_m2_steps}) steps.")

    # 6. Set Flags and Execute Move
    sequence = [{"state":"Moving"}]
    context = {
        "name":"move_to",
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context = context)

@try_wrapper
def handle_move_rel(machine, payload):
    """
    Handles the 'move_rel' command. Moves the arm relative to its
    current position by a Cartesian offset (dx, dy).
    """
    # 1. Guard Condition: Check if homed
    if not check_homed(machine):
        return

    # 2. Extract and Validate Input Arguments
    args = payload.get("args", {})
    dx = args.get("dx")
    dy = args.get("dy")

    if dx is None or dy is None:
        send_problem(machine, "Missing 'dx' or 'dy' in command arguments.")
        return

    try:
        dx = float(dx)
        dy = float(dy)
    except ValueError:
        send_problem(machine, "Invalid offset format; 'dx' and 'dy' must be numbers.")
        return

    # 3. Get Current Cartesian Position using Forward Kinematics
    # This is the key step for a relative move.
    current_m1_steps = machine.flags.get('current_m1_steps', 0)
    current_m2_steps = machine.flags.get('current_m2_steps', 0)
    
    current_theta1, current_theta2 = kinematics.steps_to_degrees(machine, current_m1_steps, current_m2_steps)
    x_current, y_current = kinematics.forward_kinematics(machine, current_theta1, current_theta2)
    
    machine.log.info(f"Current position: ({x_current:.3f}, {y_current:.3f})cm. Applying offset ({dx}, {dy}).")

    # 4. Calculate Target Cartesian Position
    x_target = x_current + dx
    y_target = y_current + dy

    # 5. Convert Target Position back to Motor Steps using Inverse Kinematics
    target_angles = kinematics.inverse_kinematics(machine, x_target, y_target)

    if target_angles is None:
        send_problem(machine, f"Inverse kinematics failed. Target ({x_target:.2f}, {y_target:.2f}) may be unreachable.")
        return
    
    theta1_target, theta2_target = target_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1_target, theta2_target)
    
    # 6. Set Context and Start the Sequencer
    sequence = [{"state": "Moving"}]
    context = {
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context=context)

def handle_dispense(machine, payload):
    if not check_homed(machine): return
    
    args = payload.get('args',{})
    pump = args.get('pump',None)
    vol = args.get('vol',None)
    
    if pump not in machine.config['pump_offsets']:
        send_problem(machine, f"Invalid pump specified: {pump}. Choose from {list(machine.config["pump_offsets"].keys())}")
        return

    # Round volume down to the nearest increment
    increment = machine.config['pump_timings']['increment_ul']
    cycles = int(vol // increment)
    if cycles * increment != vol:
        machine.log.warning(f"Volume {vol}uL not a multiple of {increment}uL. Dispensing {cycles * increment}uL.")

    if cycles <= 0:
        send_problem(machine, "Volume is too low to dispense.")
        return
        
    # This command uses the state sequencer.
    # For now, we'll just set the flags and transition directly.
    # A real implementation would calculate an offset move first.
    machine.log.info(f"Dispense command accepted for pump {pump}, {cycles} cycles.")
    machine.flags['dispense_pump'] = pump
    machine.flags['dispense_cycles'] = cycles
    machine.go_to_state('Dispensing')

def handle_dispense_at(machine, payload):
    if not check_homed(machine): return
    
    # This is the most complex handler. It sets up a multi-state sequence.
    # 1. Validate all parameters
    # 2. Calculate target motor steps from x, y
    # 3. Set machine.flags['target..._steps']
    # 4. Set machine.flags['dispense_pump'] and ['dispense_cycles']
    # 5. Set the sequencer flag: machine.flags['on_move_complete'] = 'Dispensing'
    # 6. Go to the first state in the sequence: machine.go_to_state('Moving')
    
    send_problem(machine, "dispense_at not yet implemented.")

def handle_steps(machine, payload):
    """
    Handles the low-level 'steps' command for relative motor movement.
    This command bypasses the standard homing and safety checks.
    """
    m1_rel_steps = payload.get('m1', 0)
    m2_rel_steps = payload.get('m2', 0)

    # Calculate the absolute target position from the current position
    # AI may be thinking absolute positions, so this is modified
    target_m1 = machine.flags['current_m1_steps'] + m1_rel_steps
    target_m2 = machine.flags['current_m2_steps'] + m2_rel_steps
    # target_m1 = m1_rel_steps
    # target_m2 = m2_rel_steps

    machine.log.info(f"Steps command accepted. Moving to ({target_m1}, {target_m2}).")
    
    # Set the flags that the 'Moving' state will use
    machine.flags['target_m1_steps'] = target_m1
    machine.flags['target_m2_steps'] = target_m2
    machine.flags['on_move_complete'] = 'Idle' # Tell the sequencer to return to Idle when done

    machine.go_to_state('Moving')


@try_wrapper
def handle_move_tip_to(machine, payload):
    """
    Moves the specified tool tip (e.g., a pump nozzle) to an absolute
    (x, y) coordinate.

    This is a non-trivial calculation because the tip's offset from the arm's
    center is rotated by the end-effector. The orientation of the end-effector
    is determined by the final motor angle, theta2. This creates a circular
    dependency, which we solve with a two-pass iterative approach.
    """
    if not check_homed(machine): return

    # 1. Extract and Validate Arguments
    args = payload.get("args", {})
    x_tip = args.get("x")
    y_tip = args.get("y")
    pump_key = args.get("pump")

    if x_tip is None or y_tip is None or pump_key is None:
        send_problem(machine, "Missing 'x', 'y', or 'pump' in command arguments.")
        return

    pump_offset = machine.config['pump_offsets'].get(pump_key)
    if pump_offset is None:
        send_problem(machine, f"Invalid pump key '{pump_key}'.")
        return
        
    dx = pump_offset['dx']
    dy = pump_offset['dy']

    # --- Pass 1: "Guess" the final orientation ---
    # We perform an initial inverse kinematics solve for the *tip's* target
    # position. This is not the correct final answer, but it gives us a
    # very good estimate of what the final theta2 angle will be.
    machine.log.info(f"Move Tip Pass 1: Estimating orientation for tip target ({x_tip}, {y_tip}).")
    guessed_angles = kinematics.inverse_kinematics(machine, x_tip, y_tip)
    if guessed_angles is None:
        send_problem(machine, "Target position is likely unreachable (IK Pass 1 failed).")
        return
    
    _theta1_guess, theta2_guess = guessed_angles
    machine.log.info(f"Pass 1 result: Estimated orientation angle (theta2) = {theta2_guess:.2f} degrees.")

    # --- 2. Calculate the Corrected Center Target ---
    # Now, we use the estimated orientation (theta2_guess) to rotate the
    # local pump offset vector into the global coordinate frame.
    orientation_rad = math.radians(theta2_guess)
    cos_theta = math.cos(orientation_rad)
    sin_theta = math.sin(orientation_rad)
    
    # Standard 2D rotation matrix application
    x_offset_rotated = dx * cos_theta - dy * sin_theta
    y_offset_rotated = dx * sin_theta + dy * cos_theta
    
    # The arm's center must be positioned such that: Center + RotatedOffset = Tip.
    # Therefore, the target for the center is: Center = Tip - RotatedOffset.
    x_center_target = x_tip - x_offset_rotated
    y_center_target = y_tip - y_offset_rotated
    machine.log.info(f"Corrected center target is ({x_center_target:.3f}, {y_center_target:.3f}).")

    # --- Pass 2: "Refine" the final solution ---
    # We solve the IK again, this time for the corrected center target. This
    # will yield the final, accurate motor angles.
    machine.log.info("Move Tip Pass 2: Solving final IK for corrected center target.")
    final_angles = kinematics.inverse_kinematics(machine, x_center_target, y_center_target)
    if final_angles is None:
        send_problem(machine, "Target position is unreachable (IK Pass 2 failed). This can happen near kinematic boundaries.")
        return
        
    final_theta1, final_theta2 = final_angles

    # --- 3. Execute the Move using the Sequencer ---
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, final_theta1, final_theta2)
    machine.log.info(f"IK success. Final Target Angles: ({final_theta1:.2f}, {final_theta2:.2f}) -> Steps: ({target_m1_steps}, {target_m2_steps}).")

    # Use the sequencer context, NOT machine.flags, for consistency.
    sequence = [{"state": "Moving"}]
    context = {
        "name": "move_tip_to",
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context=context)