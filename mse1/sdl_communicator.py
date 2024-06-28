import json
import asyncio
from .utility import check_if_microcontroller

if check_if_microcontroller():
    import usb_cdc # type: ignore
else:
    import serial

class sdlCommunicator:
    """
    Handles serial communication between a microcontroller (subsystem) and host
    
    Attributes:
        subsystem_name (str): The name of the subsystem or none for HOST
        port (str): The name of the serial port (e.g. COM5)
    """

    valid_comm_types = [
        "NOTIFY", "RESPONSE", "ALERT", "REQUEST", "LOG", "SYNC"
    ]

    def __init__(self,subsystem_name = None, port = None):
        self.is_microcontroller = check_if_microcontroller()
        self.subsystem_name = subsystem_name
        self.timeout = 1.5
        self.baudrate = 115200
        self.writebuffer = bytearray()
        self.readbuffer = "" # Right now this is decoded in read_serial_data
        if not self.is_microcontroller:
            self.serial = serial.Serial(port,baudrate = self.baudrate, timeout = self.timeout)

    async def test(self, interval):
        while True:
            self.writebuffer = self.create_json_message("LOG", "ok", "working").encode()
            await asyncio.sleep(interval)
    
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
    
    async def read_serial_data(self):
        """
        Reads data from the serial line, checks if it is valid JSON, and stores it.

        Args:
            port (Serial): Which subsystem is the host listening to (subsystems should set port = None)

        Returns:
            bool: True if a valid JSON message was read and stored, False otherwise.
        """
        while True:
            rawdata = bytearray()
            if self.is_microcontroller:
                if usb_cdc.data.connected and usb_cdc.data.in_waiting > 0:
                    rawdata = usb_cdc.data.readline()
            else:
                rawdata = self.serial.readline()
                    

            if rawdata != bytearray():
                try:
                    # Decode and load the JSON data
                    message = json.loads(rawdata.decode('utf-8'))
                    self.readbuffer = message
                    
                except:
                    # Store the raw message
                    self.readbuffer = {"raw":rawdata.decode()}
                    
            
            if self.readbuffer != "":
                print(self.readbuffer)
                self.readbuffer = ""
                
            await asyncio.sleep(0.1)
    
    def clearbuffers(self):
        self.readbuffer = bytearray()
        self.writebuffer = bytearray()
    
    async def write_serial_data(self):
        while True:
            if self.writebuffer != bytearray():
                if self.is_microcontroller:
                    usb_cdc.data.write(self.writebuffer + b"\r\n")
                else:
                    self.serial.write(self.writebuffer + b"\r\n")
                self.writebuffer = bytearray()
            await asyncio.sleep(0.1)

    async def subsystem_main(self):
        task1 = asyncio.create_task(self.test(10))
        task2 = asyncio.create_task(self.write_serial_data())
        task3 = asyncio.create_task(self.read_serial_data())
        await asyncio.gather(task1,task2)

    async def host_main(self):
        task1 = asyncio.create_task(self.read_serial_data())
        task2 = asyncio.create_task(self.test(7))
        task3 = asyncio.create_task(self.write_serial_data())
        await asyncio.gather(task1,task2,task3)
    

