# type: ignore
from shared_lib.statemachine import StateMachine
from communicate.circuitpython_postman import CircuitPythonPostman
from . import states

# Comments beginning with --> are notes for when this file is being used as a template

# 1. Create the state machine instance for the subsystem
# --> update `init_state` and make sure `name` is unique
machine = StateMachine(init_state='Initialize', name='STIRPLATE')

# 2. Create and attach the communication channel (Postman)
# This postman will handle the USB CDC data connection.
# --> nothing to change here.
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the defined states to the machine
# --> update this list with the correct states for your instrument
machine.add_state(states.Initialize())
machine.add_state(states.Listening())
machine.add_state(states.Stirring())
machine.add_state(states.Error())

# 4. Add flags that states might use. This pre-defines them for clarity.
# --> update this list with any flags or variables that are machine-wide
machine.add_flag('error_message', '')