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

# This dictionary maps the user-friendly channel names you specified
# to the actual attribute names on the adafruit_as7341 sensor object.
# This makes the `handle_read` function clean and easy to maintain.
CHANNEL_MAP = {
    "violet": "channel_415nm",
    "indigo": "channel_445nm",
    "blue": "channel_480nm",
    "cyan": "channel_515nm",
    "green": "channel_555nm",
    "yellow": "channel_590nm",
    "orange": "channel_630nm",
    "red": "channel_680nm",
    "clear": "channel_clear",
    "nir": "channel_nir"
}

# The list of valid gain values, as defined by the sensor's library.
VALID_GAINS = [0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

def handle_read(machine, payload):
    """Handles the 'read' command for a single color channel."""
    try:
        # Extract the channel name from the command's arguments
        channel_name = payload.get("args", [])[0].lower()
        sensor_attribute = CHANNEL_MAP.get(channel_name)

        if sensor_attribute is None:
            send_problem(machine, f"Invalid channel '{channel_name}'. Valid channels are: {list(CHANNEL_MAP.keys())}")
            return

        # Use getattr() to dynamically access the sensor property
        value = getattr(machine.sensor, sensor_attribute)
        machine.log.info(f"Read {channel_name}: {value}")

        response = Message.create_message(
            subsystem_name=machine.name,
            status="SUCCESS",
            payload={"channel": channel_name, "value": value}
        )
        machine.postman.send(response.serialize())

    except IndexError:
        send_problem(machine, "Missing argument for 'read' command. Please specify a channel.")
    except Exception as e:
        send_problem(machine, f"Error during read: {e}")

def handle_read_all(machine, payload):
    """Handles the 'read_all' command, returning all channel values."""
    try:
        all_readings = {
            name: getattr(machine.sensor, attr) for name, attr in CHANNEL_MAP.items()
        }
        machine.log.info(f"Read all channels: {all_readings}")
        response = Message.create_message(
            subsystem_name=machine.name,
            status="SUCCESS",
            payload=all_readings
        )
        machine.postman.send(response.serialize())
    except Exception as e:
        send_problem(machine, f"Error during read_all: {e}")


def handle_read_gain(machine, payload):
    """Handles the 'read_gain' command."""
    try:
        current_gain = machine.sensor.gain
        machine.log.info(f"Current gain is {current_gain}x")
        response = Message.create_message(
            subsystem_name=machine.name,
            status="SUCCESS",
            payload={"gain": current_gain}
        )
        machine.postman.send(response.serialize())
    except Exception as e:
        send_problem(machine, f"Error reading gain: {e}")


def handle_set_gain(machine, payload):
    """Handles the 'set_gain' command with validation."""
    try:
        new_gain = float(payload.get("args", [])[0])

        if new_gain not in VALID_GAINS:
            send_problem(machine, f"Invalid gain value {new_gain}. Valid gains are: {VALID_GAINS}")
            return

        machine.sensor.gain = new_gain
        machine.log.info(f"Sensor gain set to {new_gain}x")

        response = Message.create_message(
            subsystem_name=machine.name,
            status="SUCCESS",
            payload={"gain_set_to": new_gain}
        )
        machine.postman.send(response.serialize())

    except (IndexError, ValueError):
        send_problem(machine, "Invalid or missing argument for 'set_gain'. Please provide a valid number.")
    except Exception as e:
        send_problem(machine, f"Error setting gain: {e}")

def handle_led(machine, payload):
    """Handles the 'led' command to turn the illumination LED on or off."""
    try:
        # Per your request, we expect a JSON boolean (true/false).
        state = payload.get("args", [])[0]
        if not isinstance(state, bool):
            raise ValueError("Argument must be a true/false boolean.")

        machine.sensor.led = state
        status_str = "ON" if state else "OFF"
        machine.log.info(f"LED turned {status_str}")

        response = Message.create_message(
            subsystem_name=machine.name,
            status="SUCCESS",
            payload={"led_is_on": state}
        )
        machine.postman.send(response.serialize())

    except (IndexError, ValueError) as e:
        send_problem(machine, f"Invalid or missing argument for 'led'. Expected true or false. Details: {e}")
    except Exception as e:
        send_problem(machine, f"Error controlling LED: {e}")

def handle_led_intensity(machine, payload):
    """Handles the 'led_intensity' command with validation."""
    try:
        # The AS7341 library actually supports 1-20, but we will adhere
        # to the spec's requirement of 1-10 for this instrument's API.
        intensity = int(payload.get("args", [])[0])

        if not (1 <= intensity <= 10):
            send_problem(machine, f"Invalid intensity value {intensity}. Must be an integer between 1 and 10.")
            return

        machine.sensor.led_current = intensity
        machine.log.info(f"LED intensity set to {intensity}mA")

        response = Message.create_message(
            subsystem_name=machine.name,
            status="SUCCESS",
            payload={"intensity_set_to_ma": intensity}
        )
        machine.postman.send(response.serialize())

    except (IndexError, ValueError):
        send_problem(machine, "Invalid or missing argument for 'led_intensity'. Please provide an integer.")
    except Exception as e:
        send_problem(machine, f"Error setting LED intensity: {e}")