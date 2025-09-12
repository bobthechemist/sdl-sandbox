# shared_lib/command_library.py
#type: ignore
from shared_lib.messages import Message
import time

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
    machine.add_command("set_time", handle_set_time, {
        "description": "Sets the time of the microcontroller.",
        "args": ["epoch_seconds: int"]
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

def handle_set_time(machine, payload):
    """
    Sets the device's real-time clock (RTC) based on the epoch seconds 
    provided by the host.

    Args:
        machine: The main device state object (contains 'name', 'log', etc.).
        payload: The payload dictionary from the INSTRUCTION message.
    """
    try:
        # 1. Safely get the arguments from the payload
        args = payload.get("args", {})
        epoch_seconds = args.get("epoch_seconds")
        tz_offset = machine.config.get("timezone",14400) # This is a hack, needs updating

        #TODO: Figure out how to grab this information from the timestamp, which is presently not accessible to handlers
        if epoch_seconds is None or not isinstance(epoch_seconds, (int, float)):
            machine.log.info("Incorrect or missing argument in set_time.")


        # 2. Import rtc and perform the logic
        import rtc  # Local import is memory efficient
        
        # The RTC object is a singleton, get the instance
        the_rtc = rtc.RTC()
        
        # Convert epoch seconds to a time.struct_time, which the RTC requires
        new_time = time.localtime(epoch_seconds - tz_offset)
        
        # Set the RTC datetime
        the_rtc.datetime = new_time
        

        # 3. Log the success and create a success response message
        # You can format the time nicely for the log
        formatted_time = f"{new_time.tm_year}-{new_time.tm_mon:02d}-{new_time.tm_mday:02d} {new_time.tm_hour:02d}:{new_time.tm_min:02d}:{new_time.tm_sec:02d}"
        machine.log.info(f"Local time set to: {formatted_time}")
        
        response = Message.create_message(
            subsystem_name=machine.name, # Corrected: Use '=' for assignment
            status="SUCCESS",
            payload={
                "response": "Local time has been updated.",
                "time_set_to_epoch": epoch_seconds
            }
        )

    except Exception as e:
        # 4. If anything goes wrong, create a PROBLEM response
        machine.log.error(f"Failed to set time: {e}")
        response = Message.create_message(
            subsystem_name=machine.name,
            status="PROBLEM",
            payload={
                "error": "Failed to set local time.",
                "details": str(e)
            }
        )
        
    machine.postman.send(response.serialize())
