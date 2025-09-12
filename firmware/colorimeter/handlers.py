# firmware/colorimeter/handlers.py
# This file contains the handler functions for the colorimeter's custom commands.
# type: ignore
from shared_lib.messages import Message

# ============================================================================
# HELPER FUNCTIONS AND DATA
# ============================================================================

def send_problem(machine, error_msg):
    """A helper function to create and send a standardized PROBLEM message."""
    machine.log.error(error_msg)
    response = Message.create_message(
        subsystem_name=machine.name,
        status="PROBLEM",
        payload={"error": error_msg}
    )
    machine.postman.send(response.serialize())

CHANNEL_MAP = {
    "violet": "channel_415nm", "indigo": "channel_445nm", "blue": "channel_480nm",
    "cyan": "channel_515nm", "green": "channel_555nm", "yellow": "channel_590nm",
    "orange": "channel_630nm", "red": "channel_680nm", "clear": "channel_clear",
    "nir": "channel_nir"
}

VALID_GAINS = [0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

def handle_read(machine, payload):
    """Handles the 'read' command for a single color channel."""
    try:
        # --- CHANGE: Expect a dictionary for args, not a list ---
        args = payload.get("args", {})
        channel_name = args.get("channel")

        if channel_name is None:
            send_problem(machine, "Missing 'channel' argument for 'read' command.")
            return

        sensor_attribute = CHANNEL_MAP.get(channel_name.lower())
        if sensor_attribute is None:
            send_problem(machine, f"Invalid channel '{channel_name}'. Valid channels are: {list(CHANNEL_MAP.keys())}")
            return

        value = getattr(machine.sensor, sensor_attribute)
        machine.log.info(f"Read {channel_name}: {value}")
        response = Message.create_message(
            subsystem_name=machine.name, status="SUCCESS",
            payload={"channel": channel_name, "value": value}
        )
        machine.postman.send(response.serialize())
    except Exception as e:
        send_problem(machine, f"Error during read: {e}")

def handle_read_all(machine, payload):
    """Handles the 'read_all' command, returning all channel values."""
    try:
        all_readings = {name: getattr(machine.sensor, attr) for name, attr in CHANNEL_MAP.items()}
        machine.log.info(f"Read all channels: {all_readings}")
        response = Message.create_message(subsystem_name=machine.name, status="SUCCESS", payload=all_readings)
        machine.postman.send(response.serialize())
    except Exception as e:
        send_problem(machine, f"Error during read_all: {e}")

def handle_read_gain(machine, payload):
    """Handles the 'read_gain' command."""
    try:
        current_gain = machine.sensor.gain
        machine.log.info(f"Current gain is {current_gain}x")
        response = Message.create_message(subsystem_name=machine.name, status="SUCCESS", payload={"gain": current_gain})
        machine.postman.send(response.serialize())
    except Exception as e:
        send_problem(machine, f"Error reading gain: {e}")

def handle_set_gain(machine, payload):
    """Handles the 'set_gain' command with validation."""
    try:
        # --- CHANGE: Expect a dictionary for args, not a list ---
        args = payload.get("args", {})
        new_gain_str = args.get("gain")
        
        if new_gain_str is None:
            send_problem(machine, "Missing 'gain' argument for 'set_gain' command.")
            return

        new_gain = float(new_gain_str)
        if new_gain not in VALID_GAINS:
            send_problem(machine, f"Invalid gain value {new_gain}. Valid gains are: {VALID_GAINS}")
            return

        machine.sensor.gain = new_gain
        machine.log.info(f"Sensor gain set to {new_gain}x")
        response = Message.create_message(subsystem_name=machine.name, status="SUCCESS", payload={"gain_set_to": new_gain})
        machine.postman.send(response.serialize())
    except (ValueError, TypeError):
        send_problem(machine, "Invalid argument format for 'set_gain'. Please provide a valid number.")
    except Exception as e:
        send_problem(machine, f"Error setting gain: {e}")

def handle_led(machine, payload):
    """Handles the 'led' command to turn the illumination LED on or off."""
    try:
        # --- CHANGE: Expect a dictionary for args, not a list ---
        args = payload.get("args", {})
        state = args.get("state")

        if not isinstance(state, bool):
            send_problem(machine, "Argument 'state' must be a true/false boolean.")
            return

        machine.sensor.led = state
        status_str = "ON" if state else "OFF"
        machine.log.info(f"LED turned {status_str}")
        response = Message.create_message(subsystem_name=machine.name, status="SUCCESS", payload={"led_is_on": state})
        machine.postman.send(response.serialize())
    except Exception as e:
        send_problem(machine, f"Error controlling LED: {e}")

def handle_led_intensity(machine, payload):
    """Handles the 'led_intensity' command with validation."""
    try:
        # --- CHANGE: Expect a dictionary for args, not a list ---
        args = payload.get("args", {})
        intensity_str = args.get("current")

        if intensity_str is None:
            send_problem(machine, "Missing 'current' argument for 'led_intensity' command.")
            return

        intensity = int(intensity_str)
        if not (1 <= intensity <= 10):
            send_problem(machine, f"Invalid intensity value {intensity}. Must be an integer between 1 and 10.")
            return

        machine.sensor.led_current = intensity
        machine.log.info(f"LED intensity set to {intensity}mA")
        response = Message.create_message(subsystem_name=machine.name, status="SUCCESS", payload={"intensity_set_to_ma": intensity})
        machine.postman.send(response.serialize())
    except (ValueError, TypeError):
        send_problem(machine, "Invalid argument format for 'led_intensity'. Please provide an integer.")
    except Exception as e:
        send_problem(machine, f"Error setting LED intensity: {e}")