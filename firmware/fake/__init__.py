# type: ignore
from shared_lib.statemachine import StateMachine
from communicate.circuitpython_postman import CircuitPythonPostman
from . import states
from shared_lib.command_library import register_common_commands
from .handlers import handle_blink

# 1. Create the state machine instance for the "fake" subsystem
machine = StateMachine(init_state='Initialize', name='FAKE')

# 2. Create and attach the communication channel (Postman)
# This postman will handle the USB CDC data connection.
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the defined states to the machine
machine.add_state(states.Initialize())
machine.add_state(states.Idle())
machine.add_state(states.Blinking())
machine.add_state(states.Error())

# 4. Define the mahcine's command interface
register_common_commands(machine)

machine.add_command("blink", handle_blink, {
    "description": "Blinks the onboard LED.",
    "args": ["count (integer, default: 1)"]
})

# 5. Add flags that states might use. This pre-defines them for clarity.
machine.add_flag('blink_count', 0)
machine.add_flag('blink_on_time', 0.4)
machine.add_flag('blink_off_time', 0.1)
machine.add_flag('heartbeat', 5)
machine.add_flag('error_message', '')
