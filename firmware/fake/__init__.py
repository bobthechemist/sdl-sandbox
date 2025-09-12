# firmware/fake/__init__.py
# type: ignore
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman
from . import states
from firmware.common.common_states import GenericIdle
from firmware.common.command_library import register_common_commands
from .handlers import handle_blink

FAKE_CONFIG = {
    "timezone": 14400, # Hack to handle timestamp issues
}

def send_fake_device_telemetry(machine):
    """Callback function to generate and send the 'fake' device's telemetry."""
    machine.log.debug("Sending telemetry.")
    analog_value = machine.analog_in.value
    telemetry_message = Message.create_message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={"analog_value": analog_value}
    )
    machine.postman.send(telemetry_message.serialize())

# 1. Create the state machine instance
machine = StateMachine(init_state='Initialize', name='FAKE')

# 2. Attach Configuration and the Postman
machine.config = FAKE_CONFIG
postman = CircuitPythonPostpostman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the defined states
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_fake_device_telemetry))
machine.add_state(states.Blinking())
machine.add_state(states.Error())

# 4. DEFINE THE MACHINE'S COMMAND INTERFACE
register_common_commands(machine)
machine.add_command("blink", handle_blink, {
    "description": "Blinks the onboard LED.",
    "args": [
        "count (integer, default: 3)", 
        "on_time (float, default: 0.4)", 
        "off_time (float, default: 0.1)"
        ]
})

# 5. Add flags
machine.add_flag('blink_count', 0)
machine.add_flag('blink_on_time',0.4)
machine.add_flag('blink_off_time',0.1)
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 60.0)