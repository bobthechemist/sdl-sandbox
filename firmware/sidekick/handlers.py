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

def calculate_dispense_cycles(machine, volume, pump):
    """
    Calculates the number of cycles to perform to dispense liquid
    TODO: Consider implementing a calibrated volume instead of assuming 10 uL
    """
    increment = machine.config['pump_timings']['increment_ul']
    cycles = int(volume//increment)
    
    # Inform user if the requested volume is being adjusted
    if cycles * increment != volume:
        actual_vol = cycles * increment
        machine.log.warning(f"Volume {volume}uL is not a multiple of {increment}uL. Dispensing {actual_vol}uL.")

    if cycles <= 0:
        send_problem(machine, f"Volume {volume}uL is too low to dispense; must be at least {increment}uL.")
        return 0
    else:
        machine.log.info(f"{cycles} cycles of pump {pump} will be applied to dispense {volume} uL.")
        return cycles

def calculate_angles(machine, pump_key, target_x, target_y):
    """
    Returns angles needed for centering the end effector or a pump over the designated target
    """

    # Determine if centering the end effector or a pump
    pump = None
    if pump_key is not None and pump_key != 0 and pump_key != "0":
        # A number (1,2,3,4) or pump string ("p1", "p2", "p3", "p4") is valid
        pump = f"p{pump_key}" if isinstance(pump_key,int) else str(pump_key).lower()

    if pump:
        # If offsets cannot be found, then bail since pump_key was not valid
        pump_offset = machine.config['pump_offsets'].get(pump)
        dx = pump_offset['dx']
        dy = pump_offset['dy']
        if pump_offset is None:
            send_problem(machine, f"Invalid pump specified: '{pump_key}'.")
            return None
        
        # Pump Offset logic: Guess and Refine
        machine.log.info(f"Starting 2-pass move for pump '{pump}'...")
        machine.log.info(f" -> Estimating orientation for center ({target_x}, {target_y}).")
        guessed_angles = kinematics.inverse_kinematics(machine, target_x, target_y)
        if guessed_angles is None:
            send_problem(machine, "Target position is likely unreachable (IK Pass 1 failed).")
            return None
        
        _theta1_guess, theta2_guess = guessed_angles
        machine.log.info(f" -> Estimated orientation angle (theta2) = {theta2_guess:.2f} degrees.")

        orientation_rad = math.radians(theta2_guess)
        cos_theta = math.cos(orientation_rad)
        sin_theta = math.sin(orientation_rad)

        x_offset_rotated = dx * cos_theta - dy * sin_theta
        y_offset_rotated = dx * sin_theta + dy * cos_theta

        x_center_target = target_x + x_offset_rotated
        y_center_target = target_y + y_offset_rotated

        machine.log.info(f" -> Corrected center target is ({x_center_target:.3f}, {y_center_target:.3f}).")
        machine.log.info(f"Solving final IK for corrected center target.")
        target_angles = kinematics.inverse_kinematics(machine, x_center_target, y_center_target)
    else:
        machine.log.info(f"IK request for (x={target_x}, y={target_y})...")
        target_angles = kinematics.inverse_kinematics(machine, target_x, target_y)

    # Log an error but carry on
    if target_angles is None:
        machine.log.error("Inverse kinematics failed at end of `calculate_angles`")
    
    return target_angles

def calculate_steps_from_calibration(machine, x_cm, y_cm):
    """
    Calculates motor steps using the loaded BILINEAR coefficients.
    x_cm, y_cm: Coordinates relative to A1 (0,0)
    """
    c_m1 = machine.flags.get('cal_coeffs_m1')
    c_m2 = machine.flags.get('cal_coeffs_m2')
    
    if not c_m1 or not c_m2:
        return None 

    # --- CHANGE IS HERE ---
    # Must match the generation script: [1, x, y, xy]
    # Removed x^2 and y^2
    features = [1, x_cm, y_cm, x_cm*y_cm]
    
    # Check for mismatch (e.g., if you loaded an old quadratic file by mistake)
    if len(c_m1) != len(features):
        machine.log.error(f"Calibration mismatch: Expected {len(features)} coeffs, got {len(c_m1)}")
        return None

    m1_val = sum(f * c for f, c in zip(features, c_m1))
    m2_val = sum(f * c for f, c in zip(features, c_m2))
    
    return int(m1_val), int(m2_val)

def _apply_similarity_transform(machine, x, y):
    """
    Uses an external calibration (similarity) to adjust the target (x,y) coordinates
    """

    new_x = sum(c*v for c, v, in zip(machine.config["similarity_transform"]["x"],[1,x,y]))
    new_y = sum(c*v for c, v, in zip(machine.config["similarity_transform"]["y"],[1,x,y]))

    return new_x, new_y

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
    No calibration is performed with this routine. Position is where the sidekick 
    thinks the world coordinates are.
    """
    # 1. Guard Condition: Check if homed
    if not check_homed(machine):
        return

    # 2. Extract and Validate Input Arguments
    args = payload.get("args", {})

    target_x = args.get("x")
    target_y = args.get("y")
    pump_arg = args.get("pump")

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
    machine.log.info(f"IK request for (x={target_x}, y={target_y}, pump={pump_arg})...")
    target_angles = calculate_angles(machine, pump_arg, target_x, target_y)

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

#@try_wrapper
def handle_dispense(machine, payload):
    """
    Dispenses a specified volume from a pump at the current arm location.
    This command uses the state sequencer to execute the dispense action.
    """
    if not check_homed(machine): return
    
    # 1. Extract and Validate Arguments
    args = payload.get('args',{})
    pump = args.get('pump')
    vol = args.get('vol',None)
    
    if pump not in machine.config['pump_offsets']:
        valid_pumps = list(machine.config["pump_offsets"].keys())
        send_problem(machine, f"Invalid pump specified: {pump}. Choose from {valid_pumps}")
        return

    if vol is None:
        send_problem(machine, "Missing 'vol' in command arguments.")
        return

    # 2. Calculate Dispense Cycles
    cycles = calculate_dispense_cycles(machine, vol, pump)
        
    # 3. Set Context and Start the Sequencer
    machine.log.info(f"Dispense command accepted for pump {pump}, {cycles} cycles.")
    
    sequence = [{"state": "Dispensing"}]
    context = {
        "name": "dispense",
        "dispense_pump": pump,
        "dispense_cycles": cycles
    }
    machine.sequencer.start(sequence, initial_context=context)

#@try_wrapper
def handle_dispense_at(machine, payload):
    """
    Moves a specific pump tip to an absolute (x, y) coordinate, then
    dispenses a specified volume. This is a multi-step sequence.
    """
    if not check_homed(machine): return

    # 1. Extract and Validate All Arguments
    args = payload.get("args", {})
    target_x = args.get("x")
    target_y = args.get("y")
    pump_arg = args.get("pump")
    vol = args.get("vol")
    # Handle the two accepted forms (str|int) of pump argument
    pump = f"p{pump_arg}" if isinstance(pump_arg,int) else str(pump_arg).lower()

    if target_x is None or target_y is None or pump_arg is None or vol is None:
        send_problem(machine, "Missing 'x', 'y', 'pump', or 'vol' in command arguments.")
        return

    pump_offset = machine.config['pump_offsets'].get(pump)
    if pump_offset is None:
        send_problem(machine, f"Invalid pump key '{pump}'.")
        return

    # Perform Inverse Kinematics
    machine.log.info(f"IK request from dispense_at for (x={target_x}, y={target_y}, pump={pump})...")
    target_angles = calculate_angles(machine, pump, target_x, target_y)
    
    if target_angles is None:
        send_problem(machine, "Target position is unreachable (IK Pass 2 failed).")
        return
    
    theta1, theta2 = target_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)
    machine.log.info(f"IK success. Target: ({theta1:.2f}, {theta2:.2f}) degrees -> ({target_m1_steps}, {target_m2_steps}) steps.")

    # --- 3. Calculate the Dispense (Logic from handle_dispense) ---
    cycles = calculate_dispense_cycles(machine, vol, pump)

    # --- 4. Build the Sequence and Context ---
    # The context must contain ALL information needed for ALL steps in the sequence.
    machine.log.info(f"Dispense_at command accepted. Moving tip {pump} to ({target_x}, {target_y}) then dispensing {cycles} cycles.")
    
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
        "dispense_pump": pump,
        "dispense_cycles": cycles
    }

    # --- 5. Start the Sequencer ---
    machine.sequencer.start(sequence, initial_context=context)

@try_wrapper
def handle_steps(machine, payload):
    """
    Handles the low-level 'steps' command for relative motor movement.
    """
    # Must be homed to work properly
    if not check_homed(machine): return

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


def handle_to_well(machine, payload):
    """
    Moves end effector to a specified well on a 96-well plate.
    Prioritizes Quadratic Calibration for center moves.
    Falls back to Inverse Kinematics for pump offsets or if calibration is missing.
    """
    if not check_homed(machine):
        return

    # 1. Extract and Validate Arguments
    args = payload.get("args", {})
    well_designation = args.get("well")
    pump_arg = args.get("pump") # Can be None, 0, 1, "p1", etc.

    if well_designation is None:
        send_problem(machine, "Missing required 'well' argument.")
        return

    # 2. Parse well designation to grid indices
    parsed_indices = parse_well_designation(machine, well_designation)
    if parsed_indices is None:
        send_problem(machine, f"Invalid 'well' designation: '{well_designation}'.")
        return
    row_idx, col_idx = parsed_indices

    # 3. Calculate Well Coordinates (Plate Relative, cm)
    # A1 is (0,0) in this system
    pitch = machine.config['plate_geometry']['well_pitch_cm']
    well_x = row_idx * pitch
    well_y = col_idx * pitch
    
    machine.log.info(f"Targeting well '{well_designation}' at Plate Coords (x:{well_x:.2f}, y:{well_y:.2f})")

    target_m1_steps = None
    target_m2_steps = None

    # 4a. PATH A: Quadratic Calibration (Center / No Pump)
    # If no pump is specified, we use the direct polynomial map.
    if not pump_arg or pump_arg == 0 or pump_arg == "0":
        cal_steps = calculate_steps_from_calibration(machine, well_x, well_y)
        if cal_steps:
            target_m1_steps, target_m2_steps = cal_steps
            machine.log.info(f"Using Quadratic Calibration -> ({target_m1_steps}, {target_m2_steps}) steps")
        else:
            machine.log.warning("Quadratic calibration missing. Falling back to raw IK.")

    # 4b. PATH B: Inverse Kinematics (Fallback or Pump Offset)
    # If calibration failed OR a pump offset is required (which needs angular geometry), use IK.
    if target_m1_steps is None:
        if not machine.config.get('similarity_transform'):
             send_problem(machine, "Cannot use to_well; missing calibration (Similarity or Quadratic).")
             return

        # Apply Similarity Transform (Plate cm -> World cm)
        target_x, target_y = _apply_similarity_transform(machine, well_x, well_y)
        machine.log.info(f"Using Similarity Transform -> World (x:{target_x:.2f}, y:{target_y:.2f})")

        # Call inverse kinematics to find motor angles (handles pump offsets)
        target_angles = calculate_angles(machine, pump_arg, target_x, target_y)
        if target_angles is None:
            send_problem(machine, "Inverse kinematics failed. Target may be unreachable or out of safe limits.")
            return
        
        theta1, theta2 = target_angles
        # Convert Angles to Steps
        target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)
        machine.log.info(f"IK result -> ({target_m1_steps}, {target_m2_steps}) steps")

    # 6. Set Flags and Execute Move
    sequence = [{"state":"Moving"}]
    context = {
        "name": "move_to",
        "target_m1_steps": target_m1_steps,
        "target_m2_steps": target_m2_steps
    }
    machine.sequencer.start(sequence, initial_context=context)

def handle_to_well_with_pumps(machine, payload):
    """
    Moves the end effector or a specific pump to a specified well.
    If the optional 'vol' argument is provided, it will also dispense
    that volume from the specified 'pump'.
    """
    # --- 1. Initial Setup and Guard Conditions ---
    if not check_homed(machine):
        return
    
    if not machine.config.get('similarity_transform'):
        send_problem(machine, "Cannot use to_well; missing calibration information.")
        return

    # --- 2. Extract and Validate Arguments ---
    args = payload.get("args", {})
    well_designation = args.get("well")
    pump_arg = args.get("pump")  # Can be None, 0, "p1", etc.
    vol = args.get("vol")      # Optional volume in uL

    if well_designation is None:
        send_problem(machine, "Missing required 'well' argument.")
        return
        
    # If volume is specified, a pump must also be specified.
    if vol is not None and pump_arg is None:
        send_problem(machine, "Missing 'pump' argument; required when 'vol' is provided.")
        return

    # --- 3. Calculate Target Coordinates ---
    parsed_indices = parse_well_designation(machine, well_designation)
    if parsed_indices is None:
        send_problem(machine, f"Invalid 'well' designation: '{well_designation}'.")
        return
    row_idx, col_idx = parsed_indices

    pitch = machine.config['plate_geometry']['well_pitch_cm']
    well_x = row_idx * pitch
    well_y = col_idx * pitch
    machine.log.info(f"Targeting well '{well_designation}' at (x:{well_x:.2f}, y:{well_y:.2f}) cm")
    
    # Apply calibration to get the real-world target
    target_x, target_y = _apply_similarity_transform(machine, well_x, well_y)
    machine.log.info(f"After transformation: (x:{target_x:.2f}, y:{target_y:.2f})")

    # --- 4. Calculate Motor Steps for the Move ---
    target_angles = calculate_angles(machine, pump_arg, target_x, target_y)
    if target_angles is None:
        send_problem(machine, "Inverse kinematics failed. Target may be unreachable.")
        return
    
    theta1, theta2 = target_angles
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)
    machine.log.info(f"IK success. Target: ({theta1:.2f}, {theta2:.2f}) degrees -> ({target_m1_steps}, {target_m2_steps}) steps.")

    # --- 5. Conditional Logic for Dispensing ---
    if vol is not None:
        # This block executes if a volume is provided, creating a two-part sequence.
        
        # a. Format pump argument and calculate dispense cycles
        pump = f"p{pump_arg}" if isinstance(pump_arg, int) else str(pump_arg).lower()
        if pump not in machine.config['pump_offsets']:
            send_problem(machine, f"Invalid pump specified: {pump_arg}.")
            return
            
        cycles = calculate_dispense_cycles(machine, vol, pump)
        if cycles <= 0:
            # calculate_dispense_cycles already sent a specific error message.
            return

        # b. Build the two-state sequence and context
        machine.log.info(f"Move and dispense command accepted. Moving to {well_designation}, then dispensing {vol}uL from {pump}.")
        sequence = [
            {"state": "Moving"},
            {"state": "Dispensing"}
        ]
        context = {
            "name": "to_well_and_dispense",
            "target_m1_steps": target_m1_steps,
            "target_m2_steps": target_m2_steps,
            "dispense_pump": pump,
            "dispense_cycles": cycles
        }
    else:
        # This block executes if no volume is provided, performing only a move.
        machine.log.info(f"Move-only command accepted for well {well_designation}.")
        sequence = [{"state": "Moving"}]
        context = {
            "name": "to_well",
            "target_m1_steps": target_m1_steps,
            "target_m2_steps": target_m2_steps
        }

    # --- 6. Start the Sequencer ---
    machine.sequencer.start(sequence, initial_context=context)