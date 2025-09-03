# firmware/diystirplate/__init__.py
# # type: ignore
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman
from . import states
from firmware.common.common_states import GenericIdle, GenericError
from firmware.common.command_library import register_common_commands
from .handlers import *

# Comments beginning with --> are notes for when this file is being used as a template

# Functions that the machine needs to be aware of upon instantiation
def send_telemetry(machine):
    """Callback function to generate and send device's telemetry"""
    machine.log.debug("Sending telemetry")
    telemetry_message = Message.create_message(
        subsystem_name = machine.name,
        status = "TELEMETRY",
        payload={"value": 1}
    )
    machine.postman.send(telemetry_message.serialize())


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
machine.add_state(GenericIdle(telemetry_callback=send_telemetry))
machine.add_state(states.Stirring())
machine.add_state(GenericError())

# 4. Define the machine's command interface
register_common_commands(machine)
machine.add_command("on",handle_on, {
    "description": "Turns the stir plate on.",
    "args": None
})
machine.add_command("off", handle_off, {
    "description": "Turns the stirplate off.",
    "args": None
})

# 4. Add flags that states might use. This pre-defines them for clarity.
# --> update this list with any flags or variables that are machine-wide
machine.add_flag('error_message', '')