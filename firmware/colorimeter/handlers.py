# firmware/colorimeter/handlers.py
# This file contains the handler functions for the colorimeter's custom commands.
# type: ignore
from shared_lib.messages import Message
from shared_lib.error_handling import send_problem, try_wrapper
import time

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
# Note, AS7341 firmware has a but and the lowest gain (0.5x) requires that we set the gain to 0.
VALID_GAINS = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@try_wrapper
def handle_read(machine, payload):
    """Handles the 'read_all' command, returning all channel values."""
    all_readings = machine.sensor.all_channels
    machine.log.info(f"Read all channels: {all_readings}")
    response = Message.create_message(
        subsystem_name=machine.name,
        status="DATA_RESPONSE",
        payload={
            "metadata":{
                "data_type": "unknown"
            },
            "data":all_readings
        }
    )
    machine.postman.send(response.serialize())


def handle_get(machine, payload):
    """Handles the 'get' command."""
    # Populate data with gain, led status and led_intensity
    data = {}
    data["gain"] = machine.sensor.gain
    data["led_status"] = machine.sensor.led
    data["led_intensity"] = machine.sensor.led_current
    payload = {
        "meta":{
            "data_type":"dict",
            "timestamp":time.time(),
        },
        "data":data
    }
    response = Message(
        subsystem_name=machine.name,
        status = "DATA_RESPONSE",
        payload = payload
    )
    machine.postman.send(response.serialize())
 
@try_wrapper
def handle_set(machine, payload):
    """Sets relevant parameters."""
    args = payload.get("args", {})

    if "gain" in args:
        new_gain = args.get("gain", -1)

        if new_gain not in VALID_GAINS:
            send_problem(machine, f"Invalid gain value {new_gain}. Valid gains are: {VALID_GAINS}.")
        else:
            machine.sensor.gain = new_gain
            machine.log.info(f"Sensor gain set to {new_gain}.")

            response = Message.create_message(
                subsystem_name = machine.name,
                status="SUCCESS",
                payload={
                    "message": f"Gain set to {new_gain}."
                }    
            )
            machine.postman.send(response.serialize())
    if "led" in args:
        machine.sensor.led = args["led"]
        led_status = "ON" if machine.sensor.led else "OFF"
        response = Message(
            subsystem_name = machine.name,
            status="SUCCESS",
            payload={
                "message": f"The colorimeter LED is now {led_status}"
            }
        )
        machine.postman.send(response.serialize())



#TODO: Simplify these handlers so that there is one set command which accepts different arguments
#  such as led (true/false), gain(VALID_GAINS) and intensity (0-10)
# def handle_set_gain(machine, payload):
#     """Handles the 'set_gain' command with validation."""
#     try:
#         new_gain = float(payload.get("args", {})["gain"])

#         if new_gain not in VALID_GAINS:
#             send_problem(machine, f"Invalid gain value {new_gain}. Valid gains are: {VALID_GAINS}")
#             return

#         machine.sensor.gain = new_gain
#         machine.log.info(f"Sensor gain set to {new_gain}x")

#         response = Message.create_message(
#             subsystem_name=machine.name,
#             status="SUCCESS",
#             payload={"gain_set_to": new_gain}
#         )
#         machine.postman.send(response.serialize())

#     except (IndexError, ValueError):
#         send_problem(machine, "Invalid or missing argument for 'set_gain'. Please provide a valid number.")
#     except Exception as e:
#         send_problem(machine, f"Error setting gain: {e}")

def handle_led(machine, payload):
    """Handles the 'led' command to turn the illumination LED on or off."""
    try:
        
        state = payload.get("args", {})['state']

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
        intensity = int(payload.get("args", {})['intensity'])

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