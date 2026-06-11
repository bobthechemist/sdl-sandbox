# firmware/buzzer_v1/handlers.py
# type: ignore
from shared_lib.messages import send_problem, send_success
from shared_lib.error_handling import try_wrapper

@try_wrapper
def handle_motor_on(machine, payload):
    """
    Handles turning the motor on. Since the state is continuous and blocking
    other sequence actions is not necessary, we initiate a direct state transition.
    """
    if machine.state.name == "Buzzing" or machine.flags.get('is_active', False):
        send_success(machine, "Motor is already on.")
        return
    
    # State transition triggers hardware actions gracefully in Buzzing.enter()
    machine.go_to_state("Buzzing")
    send_success(machine, "Motor turned on successfully.")

@try_wrapper
def handle_motor_off(machine, payload):
    """
    Handles turning the motor off.
    """
    if machine.state.name != "Buzzing":
        send_success(machine, "Motor is already off.")
        return
    
    # State transition handles turning hardware off via Buzzing.exit()
    machine.go_to_state("Idle")
    send_success(machine, "Motor turned off successfully.")

@try_wrapper
def handle_set_effect(machine, payload):
    """
    Updates the DRV2605 effect ID. Guarded to ensure motor is currently off.
    """
    if machine.flags.get('is_active', False) or machine.state.name == "Buzzing":
        send_problem(machine, "Motor must be off to set the effect.")
        return

    # 1. Extract arguments
    args = payload.get("args", {})
    effect = args.get("effect", machine.config["operational_parameters"]["effect"])

    # 2. Type validation
    try:
        effect = int(effect)
    except ValueError:
        send_problem(machine, "Effect must be an integer.")
        return

    # 3. Limit checks
    limits = machine.config["safe_limits"]
    if not (limits["min_effect"] <= effect <= limits["max_effect"]):
        send_problem(machine, f"Effect must be between {limits['min_effect']} and {limits['max_effect']}.")
        return

    # 4. Apply changes
    machine.hardware['drv'].sequence[0] = effect
    machine.flags['current_effect'] = effect
    
    send_success(machine, f"Effect successfully set to {effect}.")