"""
message validation and encoding/decoding functions

A `message` is defined as an object in dict or JSON format that contains four pieces of information
- the source of the message
- the type of message
- a result
- a context-specific payload, which may be text or json-formatted data
"""
import json
import sys


valid_comm_types = [
    "NOTIFY", "RESPONSE", "ALERT", "REQUEST", "LOG", "SYNC"
]

valid_status = [
    "SUCCESS", "FAILED", "UNKNOWN", "NA"
]

def make_message(subsystem_name: str, comm_type: str, status: str, payload: str, jsonq = True):
    """
    Creates a message with the given information in either json or dict format.

    Args:
        subsystem_name (str): Name of subsystem sending message
        comm_type (str): Type of message.
        status (str): Status of message.
        payload (str): message content, str or JSON
        jsonq (boolean): Whether to return json (default) or dict.

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
    Processes payload. 
    - A string is split by spaces, first word is assumed to be function and the remaining
        terms are arguments.
    - Checks if arguments are in keyword format and processes them as such.
    - Checks if content is JSON and returns a function call and argument dict
    """
    return_val = []
    # check to make sure payload is a string
    if isinstance(payload, str):
        # next see if we have json and process as such
        try:
            return_dict=json.loads(payload)
            print("DEBUG: json found")
        # otherwise, process as a regular string
        except ValueError:
            print("DEBUG: Treating as a string")
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
    storage system for messages
    """
    def __init__(self):
        self.messages = []
    
    def is_empty(self):
        if len(self.messages) == 0:
            return True
        else:
            return False
    
    def store_message(self, content):
        '''
        Limit content of buffer to Dict
        '''
        if isinstance(content,dict):
            self.messages.append(content)
        else:
            raise ValueError(f"Content should be a dict but appears to be {type(content)}")

    def get_oldest_message(self, jsonq = True):
        '''
        Returns the last message in the buffer. Buffer contains dict, but json is returned by default to be consistent with make_message
        '''
        try:
            message = self.messages.pop(0)
        except IndexError:
            message = make_message("unknown", "ALERT", "FAILED", "Trying to read an empty buffer",jsonq=False)
        
        if jsonq:
            return json.dumps(message)
        else:
            return message
    
    
    def json_to_dict(self, message_json):
        try:
            message_dict = json.loads(message_json)
        except:
            message_dict = {"raw":message_json}
        return message_dict
    
    def dict_to_json(self, message_dict):
        return json.dumps(message_dict)

    
    def get_size_of_buffer(self):
        return sys.getsizeof(self.messages)
    
    def store_json(self, json_message):
        content = self.json_to_dict(json_message)
        self.store_message(content)

