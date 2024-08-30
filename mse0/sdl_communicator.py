# type: ignore
from .utility import check_if_microcontroller
from .messages import MessageBuffer, make_message

# Import appropriate modules based on the environment
if check_if_microcontroller():
    import usb_cdc # type: ignore
else:
    import serial
    

class sdlCommunicator:
    """
    facilitates communication between subsystem and host. Maintains communication buffer
    """
    def __init__(self, subsystem_name = None, port = None, baudrate = 115200, timeout = 0.5):
        """
        Args:
            subsystem_name (str): name of the subsystem, if not provided, assume host.
            port (str): Serial port for a subsystem. Host will require one of these for each subsystem; subsystems leave as None
        """
        self.is_microcontroller = check_if_microcontroller()
        self.subsystem_name = subsystem_name
        self.writebuffer = MessageBuffer()
        self.readbuffer = MessageBuffer()
        if not self.is_microcontroller:
            self.serial = serial.Serial(port, baudrate = baudrate, timeout = timeout)
    
    def read_serial_data(self):
        rawdata = bytearray()
        if self.is_microcontroller:
            if usb_cdc.data.connected and usb_cdc.data.in_waiting > 0:
                rawdata = usb_cdc.data.readline()
        else:
            rawdata = self.serial.readline()
        
        if rawdata != bytearray():
            self.readbuffer.store_json(rawdata.decode('utf-8'))
    
    def write_serial_data(self):
        if not self.writebuffer.is_empty():
            message_json = self.writebuffer.get_oldest_message(jsonq=True) 
            message_json_cr = self.prep_message_for_write(message_json) # Adds linefeed to message
            if self.is_microcontroller:
                usb_cdc.data.write(message_json_cr)
            else:
                self.serial.write(message_json_cr)
    
    def prep_message_for_write(self, message):
        message = message + '\r\n'
        return message.encode('utf-8')
    
    def close(self):
        if self.is_microcontroller:
            # Not sure if this can be closed, skipping
            pass
        else:
            self.serial.close()
        # clear out buffers
        self.writebuffer.flush()
        self.readbuffer.flush()
    


