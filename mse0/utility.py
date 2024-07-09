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