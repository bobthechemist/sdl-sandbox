# firmware/sidekick/handlers.py
# type: ignore
from shared_lib.messages import Message, send_problem, send_success
from . import kinematics
import math
from shared_lib.error_handling import try_wrapper
import re


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

def parse_well_designation(machine, well_str: str):
    """
    Parses a well string (e.g., 'B6') into zero-based (row, column) indices.
    Returns a tuple or None if invalid.
    """
    if not isinstance(well_str, str): return None
    
    plate_geo = machine.config['plate_geometry']
    rows = plate_geo['rows']
    
    sanitized_well = well_str.upper().strip()
    # Build a regex dynamically from the config
    match = re.match(r'^([' + rows + '])([1-9]|1[0-2])$', sanitized_well)
    
    if not match: return None

    letter_part = match.group(1)
    number_part = int(match.group(2))
    
    row_index = rows.find(letter_part)
    col_index = number_part - 1
    
    return (row_index, col_index)

def _calculate_steps_from_xy_quadratic(machine, x, y):
    """
    Converts (x, y) coordinates in cm to (m1, m2) motor steps using the
    loaded quadratic calibration coefficients. This is a NumPy-free function.

    Returns a tuple (m1, m2) or None on failure.
    """
    coeffs_m1 = machine.flags.get('cal_coeffs_m1')
    coeffs_m2 = machine.flags.get('cal_coeffs_m2')

    if not coeffs_m1 or not coeffs_m2:
        return None # Cannot calculate if coefficients aren't loaded

    # Build the feature vector: [1, x, y, x^2, x*y, y^2]
    features = [1, x, y, x*x, x*y, y*y]
    
    # Perform dot product manually for each motor
    m1_steps = sum(f * c for f, c in zip(features, coeffs_m1))
    m2_steps = sum(f * c for f, c in zip(features, coeffs_m2))
    
    machine.log.debug(f"Steps calculated using _calculate_steps_from_xy_quadratic: {(int(round(m1_steps)), int(round(m2_steps)))}")
    return (int(round(m1_steps)), int(round(m2_steps)))

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@try_wrapper    
def handle_home(machine, payload):
    # Monolithic and needs updating, but this method works, so refactoring not a high priority
    machine.log.info("Home command received.")
    machine.go_to_state('Homing')

@try_wrapper
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

@try_wrapper
def handle_dispense(machine, payload):
    """
    Dispenses a specified volume from a pump at the current arm location.
    This command uses the state sequencer to execute the dispense action.
    """
    if not check_homed(machine): return
    
    # 1. Extract and Validate Arguments
    args = payload.get('args',{})
    pump = args.get('pump')
    vol = args.get('vol')
    
    if pump not in machine.config['pump_offsets']:
        valid_pumps = list(machine.config["pump_offsets"].keys())
        send_problem(machine, f"Invalid pump specified: {pump}. Choose from {valid_pumps}")
        return

    if vol is None:
        send_problem(machine, "Missing 'vol' in command arguments.")
        return

    # 2. Calculate Dispense Cycles
    increment = machine.config['pump_timings']['increment_ul']
    cycles = int(vol // increment)

    # Inform user if the requested volume is being adjusted
    if cycles * increment != vol:
        actual_vol = cycles * increment
        machine.log.warning(f"Volume {vol}uL is not a multiple of {increment}uL. Dispensing {actual_vol}uL.")

    if cycles <= 0:
        send_problem(machine, f"Volume {vol}uL is too low to dispense; must be at least {increment}uL.")
        return
        
    # 3. Set Context and Start the Sequencer
    machine.log.info(f"Dispense command accepted for pump {pump}, {cycles} cycles.")
    
    sequence = [{"state": "Dispensing"}]
    context = {
        "name": "dispense",
        "dispense_pump": pump,
        "dispense_cycles": cycles
    }
    machine.sequencer.start(sequence, initial_context=context)

@try_wrapper
def handle_dispense_at(machine, payload):
    """
    Moves a specific pump tip to an absolute (x, y) coordinate, then
    dispenses a specified volume. This is a multi-step sequence.
    """
    if not check_homed(machine): return

    # 1. Extract and Validate All Arguments
    args = payload.get("args", {})
    x_tip = args.get("x")
    y_tip = args.get("y")
    pump_key = args.get("pump")
    vol = args.get("vol")

    if x_tip is None or y_tip is None or pump_key is None or vol is None:
        send_problem(machine, "Missing 'x', 'y', 'pump', or 'vol' in command arguments.")
        return

    pump_offset = machine.config['pump_offsets'].get(pump_key)
    if pump_offset is None:
        send_problem(machine, f"Invalid pump key '{pump_key}'.")
        return
        
    # --- 2. Calculate the Move (Logic from handle_move_tip_to) ---
    dx, dy = pump_offset['dx'], pump_offset['dy']

    # Pass 1: "Guess" the orientation
    guessed_angles = kinematics.inverse_kinematics(machine, x_tip, y_tip)
    if guessed_angles is None:
        send_problem(machine, "Target position is likely unreachable (IK Pass 1 failed).")
        return
    _theta1_guess, theta2_guess = guessed_angles

    # Calculate the Corrected Center Target
    orientation_rad = math.radians(theta2_guess)
    cos_theta, sin_theta = math.cos(orientation_rad), math.sin(orientation_rad)
    x_offset_rotated = dx * cos_theta - dy * sin_theta
    y_offset_rotated = dx * sin_theta + dy * cos_theta
    x_center_target = x_tip - x_offset_rotated
    y_center_target = y_tip - y_offset_rotated

    # Pass 2: "Refine" the final solution
    final_angles = kinematics.inverse_kinematics(machine, x_center_target, y_center_target)
    if final_angles is None:
        send_problem(machine, "Target position is unreachable (IK Pass 2 failed).")
        return
    final_theta1, final_theta2 = final_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, final_theta1, final_theta2)

    # --- 3. Calculate the Dispense (Logic from handle_dispense) ---
    increment = machine.config['pump_timings']['increment_ul']
    cycles = int(vol // increment)

    if cycles * increment != vol:
        actual_vol = cycles * increment
        machine.log.warning(f"Volume {vol}uL is not a multiple of {increment}uL. Dispensing {actual_vol}uL.")

    if cycles <= 0:
        send_problem(machine, f"Volume {vol}uL is too low to dispense; must be at least {increment}uL.")
        return
        
    # --- 4. Build the Sequence and Context ---
    # The context must contain ALL information needed for ALL steps in the sequence.
    machine.log.info(f"Dispense_at command accepted. Moving tip {pump_key} to ({x_tip}, {y_tip}) then dispensing {cycles} cycles.")
    
    sequence = [
        {"state": "Moving"},
        {"state": "Dispensing"}
    ]
    context = {
        "name": "dispense_at",
        # Parameters for the 'Moving' state
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps,
        # Parameters for the 'Dispensing' state
        "dispense_pump": pump_key,
        "dispense_cycles": cycles
    }

    # --- 5. Start the Sequencer ---
    machine.sequencer.start(sequence, initial_context=context)

@try_wrapper
def handle_steps(machine, payload):
    """
    Handles the low-level 'steps' command for relative motor movement.
    This command bypasses the standard homing check for diagnostics.
    """
    # 1. Extract and Validate Arguments
    args = payload.get("args", {})
    m1_rel_steps = args.get("m1", 0)
    m2_rel_steps = args.get("m2", 0)

    try:
        m1_rel_steps = int(m1_rel_steps)
        m2_rel_steps = int(m2_rel_steps)
    except (ValueError, TypeError):
        send_problem(machine, "Invalid step format; 'm1' and 'm2' must be integers.")
        return

    # 2. Calculate the absolute target position from the current position
    current_m1 = machine.flags.get('current_m1_steps', 0)
    current_m2 = machine.flags.get('current_m2_steps', 0)
    
    target_m1 = current_m1 + m1_rel_steps
    target_m2 = current_m2 + m2_rel_steps

    machine.log.info(f"Steps command accepted. Moving relatively by ({m1_rel_steps}, {m2_rel_steps}) to absolute ({target_m1}, {target_m2}).")
    
    # 3. Set Context and Start the Sequencer
    sequence = [{"state": "Moving"}]
    context = {
        "name": "steps",
        "target_m1_steps": target_m1,
        "target_m2_steps": target_m2
    }
    machine.sequencer.start(sequence, initial_context=context)


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

@try_wrapper
def handle_to_well(machine, payload):
    """
    Moves the end effector to a specified well on a 96-well plate.
    The final target is adjusted based on the specified pump nozzle.
    """

    if not check_homed(machine):
        return

    if not machine.flags.get('cal_coeffs_m1'):
        send_problem(machine, "Cannot use to_well; no calibration loaded.")
        return

    # 1. Extract and Validate Arguments
    args = payload.get("args", {})
    well_designation = args.get("well")
    pump_arg = args.get("pump") # Can be None, 0, 1, "p1", etc.

    if well_designation is None:
        send_problem(machine, "Missing required 'well' argument.")
        return

    # 2. Parse well designation to grid indices and then to XY coordinates
    parsed_indices = parse_well_designation(machine, well_designation)
    if parsed_indices is None:
        send_problem(machine, f"Invalid 'well' designation: '{well_designation}'.")
        return
    row_idx, col_idx = parsed_indices

    pitch = machine.config['plate_geometry']['well_pitch_cm']
    well_x = col_idx * pitch
    well_y = row_idx * pitch
    machine.log.info(f"Targeting well '{well_designation}' at (x:{well_x:.2f}, y:{well_y:.2f}) cm")

    # 3. Determine if this is a center or pump move and get pump offset
    pump_key = None
    if pump_arg is not None and pump_arg != 0 and pump_arg != "0":
        pump_key = f"p{pump_arg}" if isinstance(pump_arg, int) else str(pump_arg).lower()

    if pump_key:
        pump_offset = machine.config['pump_offsets'].get(pump_key)
        if pump_offset is None:
            send_problem(machine, f"Invalid pump specified: '{pump_arg}'.")
            return
        
        # --- Pump Offset Logic (Method 1: Guess and Refine) ---
        machine.log.info(f"Starting 2-pass move for pump '{pump_key}'...")

        # Pass 1: "Guess" the motor steps by targeting the well with the arm's center.
        guess_steps = _calculate_steps_from_xy_quadratic(machine, well_x, well_y)
        if guess_steps is None:
            send_problem(machine, "Initial position calculation failed (Pass 1).")
            return
        
        # Use the guess to approximate the final orientation angle (theta2)
        _m1_guess, m2_guess = guess_steps
        _theta1_approx, theta2_approx = kinematics.steps_to_degrees(machine, 0, m2_guess)
        machine.log.info(f"  -> Pass 1: Approx. orientation (theta2) = {theta2_approx:.2f} deg")
        machine.log.info(f"  -> Center Target: (x:{well_x:.3f}, y:{well_y:.3f})")
        # Rotate the local pump offset vector by the approximate angle
        orientation_rad = math.radians(theta2_approx)
        cos_theta = math.cos(orientation_rad)
        sin_theta = math.sin(orientation_rad)
        dx, dy = pump_offset['dx'], pump_offset['dy']
        machine.log.info(f"  -> Translation in end-effector plane: (x:{dx}, y:{dy})")
        x_offset_rotated = dx * cos_theta - dy * sin_theta
        y_offset_rotated = dx * sin_theta + dy * cos_theta
        
        # The corrected target for the arm's CENTER is the well pos - rotated offset
        center_target_x = well_x + x_offset_rotated
        center_target_y = well_y + y_offset_rotated
        machine.log.info(f"  -> Corrected Center Target: (x:{center_target_x:.3f}, y:{center_target_y:.3f})")

        # Pass 2: "Refine" the final motor steps using the corrected center target
        final_steps = _calculate_steps_from_xy_quadratic(machine, center_target_x, center_target_y)
        if final_steps is None:
            send_problem(machine, "Final position calculation failed (Pass 2).")
            return
        machine.log.info(f"  -> Final steps: (m1:{target_m1_steps}, m2:{target_m2_steps})")
        target_m1_steps, target_m2_steps = final_steps

    else:
        # --- Center Move Logic (Simpler, one-pass) ---
        machine.log.info("Positioning arm center over well.")
        final_steps = _calculate_steps_from_xy_quadratic(machine, well_x, well_y)
        if final_steps is None:
            send_problem(machine, "Position calculation failed for center move.")
            return
        target_m1_steps, target_m2_steps = final_steps

    # 4. Execute the final move
    machine.log.info(f"Final target motor steps: ({target_m1_steps}, {target_m2_steps})")
    sequence = [{"state": "Moving"}]
    context = {
        "name": f"to_well_{well_designation}",
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context=context)