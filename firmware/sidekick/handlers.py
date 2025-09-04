# firmware/sidekick/handlers.py
# type: ignore
from shared_lib.messages import Message
# In a real implementation, a kinematics library would live in shared_lib or firmware/common
# import kinematicsfunctions as kf

# --- Utility Functions for Handlers ---
def send_problem(machine, error_msg):
    """Helper to send a standardized PROBLEM message."""
    machine.log.error(error_msg)
    response = Message.create_message(
        subsystem_name=machine.name,
        status="PROBLEM",
        payload={"error": error_msg}
    )
    machine.postman.send(response.serialize())

def check_homed(machine):
    """Guard condition to ensure the device is homed."""
    if not machine.flags.get('is_homed', False):
        send_problem(machine, "Device must be homed before this operation.")
        return False
    return True

# --- Command Handlers ---

def handle_home(machine, payload):
    machine.log.info("Home command received.")
    machine.go_to_state('Homing')

def handle_move_to(machine, payload):
    if not check_homed(machine): return
    
    # Placeholder for coordinate validation and conversion
    # target_steps = kf.inverse_kinematics(payload['x'], payload['y'])
    # if not kf.is_within_limits(target_steps):
    #     send_problem(machine, "Target coordinates are out of safe travel limits.")
    #     return
    
    # For now, we will assume target steps are provided directly for testing
    target_m1 = payload.get('m1_steps', 0)
    target_m2 = payload.get('m2_steps', 0)

    machine.log.info(f"Move_to command accepted. Target: ({target_m1}, {target_m2}) steps.")
    machine.flags['target_m1_steps'] = target_m1
    machine.flags['target_m2_steps'] = target_m2
    machine.flags['on_move_complete'] = 'Idle' # Default exit for a simple move
    machine.go_to_state('Moving')

def handle_move_rel(machine, payload):
    if not check_homed(machine): return
    # Placeholder for relative move calculation
    # target_x = machine.flags['current_x'] + payload['dx']
    # Perform validation on target_x, then convert to steps
    send_problem(machine, "move_rel not yet implemented.")

def handle_dispense(machine, payload):
    if not check_homed(machine): return
    
    pump = payload.get('pump')
    vol = payload.get('vol')
    
    if pump not in machine.config['pump_offsets']:
        send_problem(machine, f"Invalid pump specified: {pump}")
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