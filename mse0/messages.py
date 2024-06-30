"""
message validation and encoding/decoding functions
"""
import json
import sys

class MessageBuffer():
    """
    storage system for messages
    """
    def __init__(self):
        self.messages = []
        self.valid_comm_types = [
           "NOTIFY", "RESPONSE", "ALERT", "REQUEST", "LOG", "SYNC"
        ]
    
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

    def get_oldest_message(self):
        try:
            return self.messages.pop(0)
        except IndexError:
            print('Trying to read from an empty buffer') # TODO: handle error properly
            return -1
    
    def create_json_message(self, subsystem_name: str, comm_type: str, status: str, response: str):
        """
        Creates a JSON formatted message with the given information.

        Args:
            comm_type (str): Type of the communication.
            status (str): Status of the communication.
            response (dict): Response data, which itself is a JSON formatted dictionary.

        Returns:
            str: JSON formatted string with the provided data.

        Raises:
            ValueError: If comm_type is not a valid communcation type.
        """
        if comm_type not in self.valid_comm_types:
            raise ValueError(f"Invalid communication type: {comm_type}")
            
        # Create the dictionary with the provided information
        message = {
            "subsystem_name": subsystem_name,
            "comm_type": comm_type,
            "status": status,
            "response": response
        }
        
        # Convert the dictionary to a JSON formatted string
        json_message = json.dumps(message)
        
        return json_message 
    
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

