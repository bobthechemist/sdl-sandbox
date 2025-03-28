#type: ignore
import usb_cdc
from .postman import Postman

class CircuitPythonPostman(Postman):
    """
    Postman implementation for serial communication using data line in CircuitPython.
    usb_cdc.enable(console=True, data=True) belongs in boot.py
    """

    def _open_channel(self):
        """Opens the serial port."""
        return usb_cdc.data

    def _close_channel(self):
        """Closes the serial port."""
        # Nothing to do here

    def _send(self, value):
        """Sends data over the serial port."""
        message = str(value)
        if not message.endswith('\n'):
            message += '\n'
        # Assuming you want to send a string, encode it to bytes
        data = message.encode('utf-8')  # Ensure the data is encoded as bytes
        self.channel.write(data)

    def _receive(self):
        """Receives data from the serial port."""
        # Read a line of data (terminated by newline character)
        data = self.channel.readline()
        # Decode the bytes to a string, stripping any trailing whitespace
        return data.decode('utf-8').strip()

