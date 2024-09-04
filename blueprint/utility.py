"""
Generic utility functions for the software driven laboratory

Author(s): BoB LeSuer
"""
import sys

def check_if_microcontroller():
    """
    Determine if the code is running on a microcontroller using CircuitPython.

    Returns:
    bool: True if the code is running on CircuitPython, False otherwise.
    """
    try:
        if sys.implementation.name == 'circuitpython':
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

def check_key_and_type(my_dict, my_key, my_type):
    """
    Check if a given key exists in a dictionary and if its value is of a specified type.

    Parameters:
    my_dict (dict): The dictionary to check.
    my_key: The key to look for in the dictionary.
    my_type: The type to check the value against.

    Returns:
    bool: True if the key exists in the dictionary and its value is of the specified type, False otherwise.
    """
    if my_key in my_dict:
        return isinstance(my_dict[my_key],my_type)
    return False