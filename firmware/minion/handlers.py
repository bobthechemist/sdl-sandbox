# firmware/minion/handlers.py
# type: ignore
from shared_lib.messages import Message, send_problem, send_success
from shared_lib.error_handling import try_wrapper
from adafruit_drv2605 import Effect

# AS7341 Spectrograph/Colorimeter Constants
CHANNEL_NAMES = [
    "violet", "indigo", "blue", "cyan", "green",
    "yellow", "orange", "red", "clear", "nir"
]

VALID_GAINS = [0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

# ============================================================================
# MOTOR COMMAND HANDLERS
# ============================================================================

@try_wrapper
def handle_motor_on(machine, payload):
    """
    Handles turning the motor on. Initiates a state transition to Buzzing.
    """
    if machine.state.name == "Buzzing" or machine.flags.get('is_active', False):
        send_success(machine, "Motor is already on.")
        return
    
    machine.go_to_state("Buzzing")
    send_success(machine, "Motor turned on successfully.")

@try_wrapper
def handle_motor_off(machine, payload):
    """
    Handles turning the motor off. Transitions back to Idle.
    """
    if machine.state.name != "Buzzing":
        send_success(machine, "Motor is already off.")
        return
    
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
    machine.hardware['drv'].sequence[0] = Effect(effect)
    machine.flags['current_effect'] = effect
    
    send_success(machine, f"Effect successfully set to {effect}.")

# ============================================================================
# COLORIMETER COMMAND HANDLERS
# ============================================================================

@try_wrapper
def handle_read_all(machine, payload):
    """
    Handles the 'read_all' command.
    Returns a DATA_RESPONSE with a structured payload.
    """
    readings_tuple = machine.sensor.all_channels
    
    # Create descriptive dictionary for the data payload
    readings_dict = dict(zip(CHANNEL_NAMES, readings_tuple))
    machine.log.info(f"Read all channels: {readings_dict}")
    
    response = Message.create_message(
        subsystem_name=machine.name,
        status="DATA_RESPONSE",
        payload={
            "metadata": {
                "data_type": "color_spectrum",
                "units": "counts"
            },
            "data": readings_dict
        }
    )
    machine.postman.send(response.serialize())

@try_wrapper
def handle_get_settings(machine, payload):
    """
    Handles the 'get_settings' command.
    Returns current sensor settings.
    """
    settings_data = {
        "gain": machine.sensor.gain,
        "led_is_on": machine.sensor.led,
        "intensity_ma": machine.sensor.led_current
    }
    
    response = Message.create_message(
        subsystem_name=machine.name,
        status="DATA_RESPONSE",
        payload={
            "metadata": { "data_type": "sensor_settings" },
            "data": settings_data
        }
    )
    machine.postman.send(response.serialize())
 
@try_wrapper
def handle_set_settings(machine, payload):
    """
    Handles the 'set_settings' command. Can set multiple parameters at once.
    """
    args = payload.get("args", {})
    if not isinstance(args, dict) or not args:
        send_problem(machine, "Invalid or empty 'args' object provided.")
        return

    # Track parameters successfully applied
    settings_applied = []

    if "gain" in args:
        new_gain = args["gain"]
        if new_gain in VALID_GAINS:
            machine.sensor.gain = VALID_GAINS.index(new_gain)
            settings_applied.append(f"gain={new_gain}x")
        else:
            send_problem(machine, f"Invalid gain value {new_gain}. Valid gains are: {VALID_GAINS}.")
            return

    if "led" in args:
        led_state = args["led"]
        if isinstance(led_state, bool):
            machine.sensor.led = led_state
            settings_applied.append(f"led={'ON' if led_state else 'OFF'}")
        else:
            send_problem(machine, "Invalid 'led' value; must be a boolean (true/false).")
            return

    if "intensity" in args:
        intensity = args["intensity"]
        min_i = machine.config["min_intensity"]
        max_i = machine.config["max_intensity"]
        if isinstance(intensity, int) and min_i <= intensity <= max_i:
            machine.sensor.led_current = intensity
            settings_applied.append(f"intensity={intensity}mA")
        else:
            send_problem(machine, f"Invalid 'intensity'; must be an integer between {min_i} and {max_i}.")
            return

    if settings_applied:
        send_success(machine, f"Settings applied: {', '.join(settings_applied)}.")
    else:
        send_problem(machine, f"No valid parameters found in request: {args}")

# ============================================================================
# MULTI-STEP MEASUREMENT SEQUENCE HANDLER
# ============================================================================

def handle_measure(machine, payload):
    """
    Initiates a non-blocking, multi-step measurement sequence using the StateSequencer.
    """
    sequence = [
        {"state": "TurnOnLED", "label": "Powering illuminator"},
        {"state": "ReadSensor", "label": "Acquiring data"},
        {"state": "TurnOffLED", "label": "Finalizing and reporting"}
    ]
    
    machine.log.info("Starting measurement sequence...")
    machine.sequencer.start(sequence)