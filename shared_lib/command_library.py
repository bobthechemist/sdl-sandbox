# shared_lib/command_library.py
#type: ignore
from .messages import Message

# Helper function, not a class, to register common commands.
def register_common_commands(machine):
    """
    Inspects this module and registers all common commands
    with the provided state machine instance.
    """
    # In a real implementation, you would introspect or just explicitly define.
    # For clarity, we will be explicit here.
    
    machine.add_command("help", handle_help, {
        "description": "Returns a list of all supported commands.",
        "args": []
    })
    machine.add_command("ping", handle_ping, {
        "description": "Responds with 'pong' to check connectivity.",
        "args": []
    })

# --- Handler functions are now standalone ---
def handle_help(machine, payload):
    """Sends the machine's fully assembled list of supported commands."""
    machine.log.info("Help command received. Sending capabilities.")
    response = Message.create_message(
        subsystem_name=machine.name,
        status="SUCCESS",
        payload=machine.supported_commands # Get it directly from the machine
    )
    machine.postman.send(response.serialize())

def handle_ping(machine, payload):
    """Responds with a simple 'pong'."""
    machine.log.info("Ping received. Responding.")
    response = Message.create_message(
        subsystem_name=machine.name,
        status="SUCCESS",
        payload={"response": "pong"}
    )
    machine.postman.send(response.serialize())