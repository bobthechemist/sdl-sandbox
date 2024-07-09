import sys

def check_if_microcontroller():
    """
    Returns True if it appears that this code is being run on a microcontroller using CircuitPython
    """
    try:
        if sys.implementation.name == 'circuitpython':
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

def check_key_and_type(my_dict, my_key, my_type):
    if my_key in my_dict:
        return isinstance(my_dict[my_key],my_type)
    return False