# type: ignore
from shared_lib.statemachine import StateMachine
from communicate.circuitpython_postman import CircuitPythonPostman
from . import states

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

# 4. Add flags that states might use. This pre-defines them for clarity.
machine.add_flag('blink_count', 0)
machine.add_flag('error_message', '')