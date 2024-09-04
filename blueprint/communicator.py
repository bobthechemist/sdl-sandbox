# type: ignore
"""
A class to handle serial communication, adaptable for both microcontroller and non-microcontroller environments.

Author(s): BoB LeSuer
"""
from .utility import check_if_microcontroller
from .messages import MessageBuffer

# Import appropriate modules based on the environment
if check_if_microcontroller():
    import usb_cdc 
else:
    import serial
    

class Communicator:
    """
    A class to handle serial communication, adaptable for both microcontroller and non-microcontroller environments.

    Attributes:
    -----------
    is_microcontroller : bool
        Indicates if the environment is a microcontroller.
    subsystem_name : str
        Name of the subsystem, default is 'HOST'.
    writebuffer : MessageBuffer
        Buffer to store messages to be written.
    readbuffer : MessageBuffer
        Buffer to store messages that are read.
    serial : serial.Serial
        Serial communication object for non-microcontroller environments.
    """

    def __init__(self, subsystem_name='HOST', port=None, baudrate=115200, timeout=0.5):
        """
        Initializes the Communicator with the given parameters.

        Parameters:
        -----------
        subsystem_name : str, optional
            Name of the subsystem (default is 'HOST').
        port : str, optional
            Serial port to connect to (default is None).
        baudrate : int, optional
            Baud rate for the serial communication (default is 115200).
        timeout : float, optional
            Timeout for the serial communication (default is 0.5 seconds).
        """
        self.is_microcontroller = check_if_microcontroller()
        self.subsystem_name = subsystem_name
        self.writebuffer = MessageBuffer()
        self.readbuffer = MessageBuffer()
        if not self.is_microcontroller:
            self.serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
    
    def read_serial_data(self):
        """
        Reads data from the serial port and stores it in the read buffer.

        For microcontroller environments, it reads from usb_cdc. For non-microcontroller environments, it reads from the serial port.
        """
        rawdata = bytearray()
        if self.is_microcontroller:
            if usb_cdc.data.connected and usb_cdc.data.in_waiting > 0:
                rawdata = usb_cdc.data.readline()
        else:
            rawdata = self.serial.readline()
        
        if rawdata != bytearray():
            self.readbuffer.store_json(rawdata.decode('utf-8'))
    
    def write_serial_data(self):
        """
        Writes data from the write buffer to the serial port.

        For microcontroller environments, it writes to usb_cdc. For non-microcontroller environments, it writes to the serial port.
        """
        if not self.writebuffer.is_empty():
            message_json = self.writebuffer.get_oldest_message(jsonq=True) 
            message_json_cr = self.prep_message_for_write(message_json) # Adds linefeed to message
            if self.is_microcontroller:
                usb_cdc.data.write(message_json_cr)
            else:
                self.serial.write(message_json_cr)
    
    def prep_message_for_write(self, message):
        """
        Prepares a message for writing by adding a linefeed and encoding it.

        Parameters:
        -----------
        message : str
            The message to be prepared.

        Returns:
        --------
        bytes
            The encoded message with a linefeed.
        """
        message = message + '\r\n'
        return message.encode('utf-8')
    
    def close(self):
        """
        Closes the serial connection and flushes the buffers.

        For microcontroller environments, it skips closing as it's uncertain if it can be closed.
        """
        if self.is_microcontroller:
            # Not sure if this can be closed, skipping
            pass
        else:
            self.serial.close()
        # clear out buffers
        self.writebuffer.flush()
        self.readbuffer.flush()