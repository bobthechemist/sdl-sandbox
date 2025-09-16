# shared_lib/error_handling.py
# Some helper functions for consistent error handling 
from shared_lib.messages import Message


def send_problem(machine, error_msg):
    """A helper function to create and send a standardized PROBLEM message."""
    machine.log.error(error_msg)
    response = Message.create_message(
        subsystem_name=machine.name,
        status="PROBLEM",
        payload={"error": error_msg}
    )
    machine.postman.send(response.serialize())

# A decorator for wrapping try/except around logic
def try_wrapper(func):

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            machine = args[0] if args else kwargs.get('machine')
            send_problem(machine, f"The function {func.__name__} raised an error: {e}")
    #wrapper.__name__ = func.__name__
    return wrapper