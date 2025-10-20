# shared_lib/error_handling.py
# Some helper functions for consistent error handling 
from shared_lib.messages import send_problem




# A decorator for wrapping try/except around logic
# Custom information can be added by setting the err_msg variable in the function
def try_wrapper(func):

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            machine = args[0] if args else kwargs.get('machine')
            extra = getattr(func, "err_msg","nothing new")
            send_problem(machine, f"The function {func.__name__} raised an error: {e}.")
    #wrapper.__name__ = func.__name__
    return wrapper

def try_wrapper_broken(func):
    """
    A decorator for wrapping try/except around device command handlers.
    This version is compatible with CircuitPython (no functools).
    """
    def wrapper(*args, **kwargs):
        try:
            # Execute the original function
            return func(*args, **kwargs)
        except Exception as e:
            # Gracefully handle any exceptions
            machine = args[0] if args else kwargs.get('machine')
            if machine:
                # Use the manually saved function name for the error report
                send_problem(machine, f"The function '{wrapper._name_}' raised an error: {e}")

    # --- The Fix for CircuitPython ---
    # Manually copy the name from the original function to the wrapper
    wrapper._name_ = func.__name__
    return wrapper