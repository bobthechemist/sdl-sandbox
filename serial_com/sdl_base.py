import json
import usb_cdc

# Communication types
'''
NOTIFY, RESPONSE, ALERT, REQUEST, LOG, SYNC 
* NOTIFY: Periodic updates or status reports, including system updates.
* RESPOND: Replies to commands or requests, including acknowledgments.
* ALERT: Critical issues or errors.
* REQUEST: Commands or queries from the host system.
* LOG: Event logs and detailed debugging information.
* SYNC: Synchronization of time or state.
'''

class MicrocontrollerCommunicator:
    """
    A class to handle communication for a microcontroller subsystem.

    Attributes:
        subsystem_name (str): The name of the subsystem
    """
    
    valid_comm_types = [
        "NOTIFY", "RESPONSE", "ALERT", "REQUEST", "LOG", "SYNC"
    ]

    def __init__(self,subsystem_name):
        """
        Initializes the MicrocontrollerCommunicator with a subsystem name.
        
        Args:
            subsystem_name(str): The name of the subsystem.
        """
        self.subsystem_name = subsystem_name

    # TODO: Consider adding success flag in addition to status
    def create_json_message(self, comm_type, status, response):
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
        # Define the possible simplified communication types
        
        
        if comm_type not in self.valid_comm_types:
            raise ValueError(f"Invalid communication type: {comm_type}")
            
        # Create the dictionary with the provided information
        message = {
            "subsystem_name": self.subsystem_name,
            "comm_type": comm_type,
            "status": status,
            "response": response
        }
        
        # Convert the dictionary to a JSON formatted string
        json_message = json.dumps(message)
        
        return json_message
    
    def read_serial_data(self):
        """
        Reads data from the serial line, checks if it is valid JSON, and stores it.

        Returns:
            bool: True if a valid JSON message was read and stored, False otherwise.
        """
        if usb_cdc.data.connected and usb_cdc.data.in_waiting > 0:
            line = usb_cdc.data.readline()
            if line:
                try: 
                    # Decode and load the JSON data
                    message = json.loads(line.decode('utf-8'))
                    self.data_in = message
                    return True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Store the raw message
                    self.data_in = {"raw": line.decode()}
                    return False
        return False
    
    def clear_data_in(self):
        self.data_in = None
    
    def write_serial_data(self, data_out):
        usb_cdc.data.write(data_out.encode() + b"\r\n")



# Example usage
if __name__ == "__main__":
    # Initialize the communicator with the subsystem name
    communicator = MicrocontrollerCommunicator("TemperatureController")

    # Example data
    subsystem_name = "TemperatureSensor"
    comm_type = "NOTIFY"
    status = "OK"
    response = {
        "temperature": 23.5,
        "unit": "Celsius"
    }

    # Create the JSON message
    json_message = communicator.create_json_message(subsystem_name, comm_type, status, response)
    print(json_message)
