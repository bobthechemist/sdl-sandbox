import json
from .utility import check_if_microcontroller

print('got here')
class sdlCommunicator:
    def __init__(self):
        self.is_microcontroller = check_if_microcontroller()
        print(self.is_microcontroller)
        if self.is_microcontroller:
            import usb_cdc
            print('on a microcontroller')
        else:
            import serial
            print('on a host computer')

