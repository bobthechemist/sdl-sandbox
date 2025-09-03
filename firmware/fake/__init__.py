# firmware/fake/__init__.py
# type: ignore
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message # Import Message for the callback
from communicate.circuitpython_postman import CircuitPythonPostman
# Import the specific states for this device
from . import states
# --- NEW ---: Import the new generic state
from firmware.common.common_states import GenericIdle
from firmware.common.command_library import register_common_commands
from .handlers import handle_blink

# --- NEW ---: Define the device-specific heartbeat logic as a simple function.
def send_fake_device_heartbeat(machine):
    """Callback function to generate and send the 'fake' device's heartbeat."""
    machine.log.debug("Heartbeat.")
    analog_value = machine.analog_in.value # Accesses hardware specific to this machine
    heartbeat_message = Message.create_message(
        subsystem_name=machine.name,
        status="HEARTBEAT",
        payload={"analog_value": analog_value}
    )
    machine.postman.send(heartbeat_message.serialize())

# 1. Create the state machine instance
machine = StateMachine(init_state='Initialize', name='FAKE')

# 2. Attach the Postman
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the defined states
machine.add_state(states.Initialize())
# --- NEW ---: Instantiate and add the GenericIdle state, passing our callback.
machine.add_state(GenericIdle(heartbeat_callback=send_fake_device_heartbeat))
machine.add_state(states.Blinking())
machine.add_state(states.Error())

# 4. DEFINE THE MACHINE'S COMMAND INTERFACE
register_common_commands(machine)
machine.add_command("blink", handle_blink, {
    "description": "Blinks the onboard LED.",
    "args": ["count (integer, default: 1)"]
})

# 5. Add flags
machine.add_flag('blink_count', 0)
machine.add_flag('error_message', '')
machine.add_flag('heartbeat_interval', 5.0) # The generic state will use this
