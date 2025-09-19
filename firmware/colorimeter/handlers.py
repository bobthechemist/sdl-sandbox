# firmware/colorimeter/handlers.py
# This file contains the handler functions for the colorimeter's custom commands.
# type: ignore
from shared_lib.messages import Message, send_problem, send_success
from shared_lib.error_handling import try_wrapper
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
    """Handles the 'read' command, returning all channel values."""
    all_readings = machine.sensor.all_channels
    machine.log.info(f"Read all channels: {all_readings}")
    response = Message(
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
    # Populate data with gain, led status and intensity
    data = {}
    data["gain"] = machine.sensor.gain
    data["led"] = machine.sensor.led
    data["intensity"] = machine.sensor.led_current
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
    responded = False
    if "gain" in args:
        new_gain = args.get("gain", -1)

        if new_gain not in VALID_GAINS:
            send_problem(machine, f"Invalid gain value {new_gain}. Valid gains are: {VALID_GAINS}.")
        else:
            machine.sensor.gain = new_gain
            send_success(machine, f"Sensor gain set to {new_gain}")
        responded = True

    if "led" in args:
        machine.sensor.led = args["led"]
        led_status = "ON" if machine.sensor.led else "OFF"
        send_success(machine, f"The colorimeter LED is now {led_status}")
        responded = True
    if "intensity" in args:
        intensity = args["intensity"]
        min = machine.config["min_intensity"]
        max = machine.config["max_intensity"]

        if isinstance(intensity, int) and min <= intensity <= max:
            machine.sensor.intensity = intensity
            send_success(machine, f"The colorimeter LED intensity is now {machine.sensor.intensity}.")
        else:
            machine.log.error("Invalid LED intensity received")
            send_problem(machine, f"A valid intensity is an integer between {min} and {max}. Leaving intensity at {machine.sensor.intensity}")
        responded = True
    if not responded:
        # We didn't find any valid paremeters to set, so assume there was a problem in the message
        send_problem(machine, f"Something was wrong with your request, perhaps a typo? {args}")
