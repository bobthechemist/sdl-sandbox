import json
from .utility import check_if_microcontroller

if check_if_microcontroller():
    import usb_cdc
else:
    import serial

class sdlCommunicator:
    """
    Handles serial communication between a microcontroller (subsystem) and host
    
    Attributes:
        subsystem_name (str): The name of the subsystem or none for HOST
    """

    valid_comm_types = [
        "NOTIFY", "RESPONSE", "ALERT", "REQUEST", "LOG", "SYNC"
    ]

    def __init__(self,subsystem_name = None):
        self.is_microcontroller = check_if_microcontroller()
        self.subsystem_name = subsystem_name
        self.timeout = 1.5
        self.baudrate = 115200

    def test(self, portname):
        p = serial.Serial(portname,timeout = self.timeout, baudrate=self.baudrate)
        print(p.readlines())
        return True
    
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
    
    def read_serial_data(self, port = None):
        """
        Reads data from the serial line, checks if it is valid JSON, and stores it.

        Args:
            port (Serial): Which subsystem is the host listening to (subsystems should set port = None)

        Returns:
            bool: True if a valid JSON message was read and stored, False otherwise.
        """
        line = ""
        if self.is_microcontroller and usb_cdc.data.connected and usb_cdc.data.in_waiting > 0:
            line = usb_cdc.data.readline()
            
        else:
            with serial.Serial(port) as p:
                print(p.readlines())
                return True

        if line:
            try:
                # Decode and load the JSON data
                message = json.loads(line.decode('utf-8'))
                self.data_in = message
                return True
            except (json.JSONDecodeError,UnicodeDecodeError):
                # Store the raw message
                self.data_in = {"raw":line.decode()}
                return True
            
        return False
    
    def clear_data_in(self):
        self.data_in = None
    
    def write_serial_data(self, data_out, port = None):
        if self.is_microcontroller:
            usb_cdc.data.write(data_out.encode() + b"\r\n")
        else:
            port.write(data_out.encode() + b"\r\n")
