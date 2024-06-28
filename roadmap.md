# Notes and such

## where we stand

- serial_com is deprecated and is around for one or two more pushes just in case there is something useful in that folder
- mse1 has a successful implementation of async serial communication with the subsystem and host sending/receiving messages
- It should be possible to group tasks from multiple subsystems. This needs to be done on the host side and might be facilitated by overriding a basic task function in mse1.
 

- MicrocontrollerCommunicator is a class that provides basic comminication tools.
    - creates JSON message with required/recommended keys
    - Checks data line for content
    - Sends content to data line
- *Consider expanding class to be suitable for both subsystem and host*
    - One code base to maintain, will require conditional imports.
    - example solution:

``` python
class SerialHandler:
    def __init__(self):
        self.is_microcontroller = False
        try:
            import usb_cdc  # CircuitPython specific library
            self.serial = usb_cdc.data
            self.is_microcontroller = True
        except ImportError:
            import serial  # PySerial for host computer
            self.serial = serial.Serial(port='COM3', baudrate=9600)

    def write(self, data):
        if self.is_microcontroller:
            self.serial.write(data)
        else:
            self.serial.write(data.encode())  # PySerial expects bytes

    def read(self):
        if self.is_microcontroller:
            return self.serial.read()
        else:
            return self.serial.read().decode()  # PySerial returns bytes
```


* I think serial communcation from subsystem to host needs to be initialized early. Each subsystem would have its own instance on the host. This might allow for the port to remain open and avoid some of the problems I am having with timeouts and capturing all of the information.



## Tips and Tricks

* Pylance can be told to [ignore a particular line/file](https://www.reddit.com/r/VisualStudioCode/comments/i3mpct/comment/g5bkx9u/) 
    * add `type: ignore` as a comment either at the end of the line or the top of the file.
    * useful for when a script calls microcontroller imports that aren't part of the dev system.