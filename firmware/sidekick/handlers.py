# firmware/sidekick/handlers.py
# type: ignore
from shared_lib.messages import Message, send_problem, send_success
from . import kinematics
import math
from shared_lib.error_handling import try_wrapper

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

# --- Command Handlers ---
def handle_angles(machine, payload):
    """
    Moves the motors to a specified angular position (theta1, theta2)
    after validating that the target is within safe operational limits.
    """
    # 1. Guard Condition: Check if homed
    if not check_homed(machine):
        return

    # 2. Extract and Validate Input Arguments
    args = payload.get("args", {})
    theta1 = args.get("theta1")
    theta2 = args.get("theta2")

    if theta1 is None or theta2 is None:
        send_problem(machine, "Missing 'theta1' or 'theta2' in command arguments.")
        return

    try:
        theta1 = float(theta1)
        theta2 = float(theta2)
    except ValueError:
        send_problem(machine, "Invalid angle format; 'theta1' and 'theta2' must be numbers.")
        return

    # 3. Validate Against Operational Limits
    limits = machine.config['operational_limits_degrees']
    if not (limits['m1_min'] <= theta1 <= limits['m1_max']):
        msg = f"Target theta1 ({theta1}) is outside operational limits [{limits['m1_min']}, {limits['m1_max']}]."
        send_problem(machine, msg)
        return
    
    if not (limits['m2_min'] <= theta2 <= limits['m2_max']):
        msg = f"Target theta2 ({theta2}) is outside operational limits [{limits['m2_min']}, {limits['m2_max']}]."
        send_problem(machine, msg)
        return

    # 4. Convert Validated Angles to Steps
    target_m1_steps, target_m2_steps = degrees_to_steps(machine, theta1, theta2)
    machine.log.info(f"Angle command accepted. Target: ({theta1}, {theta2}) degrees -> ({target_m1_steps}, {target_m2_steps}) steps.")

    # 5. Set Flags and Execute Move
    machine.flags['target_m1_steps'] = target_m1_steps
    machine.flags['target_m2_steps'] = target_m2_steps
    machine.flags['on_move_complete'] = 'Idle'
    machine.go_to_state('Moving')
    
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

def handle_move_rel(machine, payload):
    if not check_homed(machine): return
    # Placeholder for relative move calculation
    # target_x = machine.flags['current_x'] + payload['dx']
    # Perform validation on target_x, then convert to steps
    send_problem(machine, "move_rel not yet implemented.")

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




# ... inside handlers.py, add the new function ...

@try_wrapper
def handle_move_tip_to(machine, payload):
    """
    Moves the specified tool tip (e.g., a pump nozzle) to an absolute
    (x, y) coordinate, compensating for end-effector rotation.
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

    # 2. --- Pass 1: "Guess" the orientation ---
    # Solve for the tip position to get an approximate theta2
    machine.log.info(f"Rotation Move Pass 1: Guessing IK for tip at ({x_tip}, {y_tip})")
    guessed_angles = kinematics.inverse_kinematics(machine, x_tip, y_tip)
    if guessed_angles is None:
        send_problem(machine, "Target position is unreachable (Pass 1).")
        return
    
    _theta1_guess, theta2_guess = guessed_angles
    orientation_angle_rad = math.radians(theta2_guess) # Convert to radians for math functions
    machine.log.info(f"Pass 1 result: Estimated orientation (theta2) = {theta2_guess:.2f} degrees.")

    # 3. --- Calculate the Corrected Target ---
    # Use the estimated orientation to find the true target for the arm's center
    cos_theta = math.cos(orientation_angle_rad)
    sin_theta = math.sin(orientation_angle_rad)
    
    x_offset_rotated = dx * cos_theta - dy * sin_theta
    y_offset_rotated = dx * sin_theta + dy * cos_theta
    
    x_center_target = x_tip - x_offset_rotated
    y_center_target = y_tip - y_offset_rotated
    machine.log.info(f"Corrected center target is ({x_center_target:.3f}, {y_center_target:.3f})")

    # 4. --- Pass 2: "Refine" the solution ---
    # Solve the IK for the corrected center target
    machine.log.info("Rotation Move Pass 2: Solving IK for corrected center target.")
    final_angles = kinematics.inverse_kinematics(machine, x_center_target, y_center_target)
    if final_angles is None:
        send_problem(machine, "Target position is unreachable (Pass 2). This can happen near kinematic boundaries.")
        return
        
    final_theta1, final_theta2 = final_angles

    # 5. --- Execute the Move ---
    # Convert final angles to steps and go to the Moving state
    target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, final_theta1, final_theta2)
    machine.log.info(f"IK success. Final Target Angles: ({final_theta1:.2f}, {final_theta2:.2f}) -> Steps: ({target_m1_steps}, {target_m2_steps}).")

    machine.flags['target_m1_steps'] = target_m1_steps
    machine.flags['target_m2_steps'] = target_m2_steps
    machine.flags['on_move_complete'] = 'Idle'
    machine.go_to_state('Moving')