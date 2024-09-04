"""
A message storage system for dict/json formatted information.

Author(s): BoB LeSuer
"""
import json
import sys

# The type of communication may be used to guide how the recipient uses the message
valid_comm_types = [
    "NOTIFY", "RESPONSE","REQUEST"
]

# General indicators on whether the message, or response to the message, was successful.
valid_status = [
    "SUCCESS", "FAILED", "NA"
]

def make_message(
        subsystem_name: str = None, 
        comm_type: str = "NOTIFY", 
        status: str = "NA", 
        payload: str = "", 
        jsonq: bool = False):
    """
    Creates a message with the given information in either json or dict format.

    Args:
        subsystem_name (str): Name of subsystem sending message
        comm_type (str): Type of message.
        status (str): Status of message.
        payload (str): message content, str or JSON
        jsonq (boolean): Whether to return json or dict (default).

    Returns:
        str: JSON formatted string or dict with the provided data.

    Raises:
        ValueError: If comm_type is not a valid communcation type.
        ValueError: If status is not a valid status type
    """
    # Errors stop things - perhaps forcing the generated message to have this info is preferred
    if comm_type not in valid_comm_types:
        raise ValueError(f"Invalid communication type: {comm_type}")

    if status not in valid_status:
        raise ValueError(f"Invalid status: {status}")

    # Create the dictionary with the provided information
    message = {
        "subsystem_name": subsystem_name,
        "comm_type": comm_type,
        "status": status,
        "payload": payload
    }

    # Return the desired format
    if jsonq:
        return json.dumps(message)
    else:
        return message

def parse_payload(payload):
    """
    Parses a payload string and extracts relevant information.
    
    Args:
        payload (str): The input payload string to be processed.
        
    Returns:
        dict: A dictionary containing the extracted information. The dictionary has the following keys:
            - 'func': The function name extracted from the payload.
            - Additional keys for arguments, either in keyword format (key=value) or positional format (arg1, arg2, ...).
            
    Raises:
        TypeError: If the input payload is not a string.
    """
    return_val = []
    # check to make sure payload is a string
    if isinstance(payload, str):
        # next see if we have json and process as such
        try:
            return_dict=json.loads(payload)
        # otherwise, process as a regular string
        except ValueError:
            split_payload = payload.split()
            # Converting list into dict
            return_dict = {'func':split_payload[0]}
            # Determine format of arguments, pull key names if present, generate if not
            if len(split_payload) > 1:
                args = split_payload[1::]
                arg_num = 1
                for arg in args:
                    if "=" in arg:
                        k, v = arg.split("=")
                        return_dict[k]=v
                    else:
                        return_dict[f'arg{arg_num}']=arg
                        arg_num = arg_num + 1
    else:
        raise TypeError(f"Trying to interpret a payload that is not a string. It is {type(payload)}")

    return return_dict


class MessageBuffer():
    """
    A class to manage a buffer of messages.

    Attributes:
        messages (list): A list to store messages.

    Methods:
        - __init__(): Initializes an empty message buffer.
        - is_empty(): Checks if the message buffer is empty.
        - store_message(content: dict): Stores a message in the buffer.
        - store_json(json_message: str): Stores a JSON-formatted message in the buffer.
        - get_oldest_message(jsonq: bool = False): Retrieves the oldest message from the buffer.
        - json_to_dict(message_json: str): Converts a JSON-formatted message to a dictionary.
        - dict_to_json(message_dict: dict): Converts a dictionary to a JSON-formatted message.
        - get_size_of_buffer(): Returns the size of the message buffer.
        - flush(): Clears all messages from the buffer.
    """

    def __init__(self):
        """
        Initializes an empty message buffer.
        """
        self.messages = []

    def is_empty(self):
        """
        Checks if the message buffer is empty.

        Returns:
            bool: True if the buffer is empty, False otherwise.
        """
        if len(self.messages) == 0:
            return True
        else:
            return False

    def store_message(self, content):
        """
        Stores a message in the buffer.

        Args:
            content (dict): The message content as a dictionary.

        Raises:
            ValueError: If the content is not a dictionary.
        """
        if isinstance(content,dict):
            self.messages.append(content)
        else:
            raise ValueError(f"Content should be a dict but appears to be {type(content)}")

    def store_json(self, json_message):
        """
        Stores a JSON-formatted message in the buffer.

        Args:
            json_message (str): The JSON-formatted message.

        Notes:
            Assumes that the JSON message can be converted to a dictionary.
        """        
        content = self.json_to_dict(json_message)
        self.store_message(content)

    def get_oldest_message(self, jsonq = False):
        """
        Retrieves the oldest message from the buffer.

        Args:
            jsonq (bool, optional): If True, returns the message as a JSON string. Defaults to False.

        Returns:
            dict or str: The oldest message (dictionary or JSON string) or None if the buffer is empty.
        """
        try:
            message = self.messages.pop(0)
        except IndexError:
            return None

        if jsonq:
            return json.dumps(message)
        else:
            return message

    def json_to_dict(self, message_json):
        """
        Converts a JSON-formatted message to a dictionary.

        Args:
            message_json (str): The JSON-formatted message.

        Returns:
            dict: The message content as a dictionary.
        """        
        try:
            message_dict = json.loads(message_json)
        except:
            message_dict = {"raw":message_json}
        return message_dict

    def dict_to_json(self, message_dict):
        """
        Converts a dictionary to a JSON-formatted message.

        Args:
            message_dict (dict): The message content as a dictionary.

        Returns:
            str: The JSON-formatted message.
        """        
        return json.dumps(message_dict)

    def get_size_of_buffer(self):
        """
        Returns the size of the message buffer.

        Returns:
            int: The size of the buffer in bytes.
        """        
        return sys.getsizeof(self.messages)

    def flush(self):
        """
        Clears all messages from the buffer.
        """
        self.messages = []

