# Notes and such

## 250413

- on my way to POSE
- Working on communicate, which is a generalizable package for transmitting and processing mesages.
- inbox when created in main is accessible inside and outside secretary.
- done processing a message, then file it. 
- turning subsystem router into the technician
    - (super)state machine that monitors an inbox (populated by the secretary), populates a shared outbox and operates the state machines/subsystems under its control. 
- Above isn't going to work. Technician must be a state machine and the system itself is the state machine orchestrator. This might make things a bit cleaner since the orchestrator can instantiate the inbox/outbox and such.
- Secretary populates the buffers of the state machines with their tasks, and they use that buffer to figure out what to do. They should have access to the outbox so they can deliver results.
- Secretary needs a knowledge base to figure out what to do with instructions. For example, if a system has SM that is blinking lights and a SM that is controlling pumps, then knowing which command goes to which SM will be important. Could be a simple dictionary with funtion names as keys and SMs as values.

## 240904

- Created state machine code
- Demonstration of microcontroller as finite state machine. 
- Basic documentation available for all methods.


## 240716

- Proof of concept complete - microcontroller can receive commands and execute them, returning a response
- microcontroller can send periodic notifications (although linefeed needs to be addressed in reading data)
- Jupyter notebook can connect to subsystem and send/receive information.

## 240705

- codename *blueprint* representing the core ideas and concepts
- (mse1 codename is tshirt, representing simplicity and functional)

## 240702 goals

- mse0 container class that incorporates a subsystem with the communicator. 
    Not sure this is the right approach. Might need generic ways for subsystem and communicator to interact.
    
- host and test subsystems

## where we stand

- MessageBuffer needs some rethinking. Commands related to ensure the buffer contains appropriately formatted data are there; however they are used also in cases where the buffer is not needed, so it seems a bit redundant to keep making MessageBuffer classes just for using the create_json_message routine. Alternatively, a subsystem might benefit from having its own buffer instead of hiding it in the sdlCommunicator.

- Current thinking is that a subsystem is imported from `mseX.subsystems` and then an instance (e.g. `subsystem = pumps.sdlPumps()`) is created. All instances have the basic structure of defining a dictionary of commands (might be beneficial to have a registration class, but that may be a bit much) and functions that the subsystem performs. Those functions must (1) do something and (2) say something in the form of a JSON formatted response. This latter part is debatable and might want to have this level of detail controlled by the communicator. Each subsystem has a `.run()` function that describes what the microcontroller is doing.

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

* Things are getting pretty clunky - the read/write buffers may be problematic and I don't have a clear idea of what goes on in each state. I need to trace a command from the host to the uc. The command is received by the listening state, processed in the listening state, and then the operation(abstract) state knows it is supposed to do something but doesn't know what.

## Tips and Tricks

* Pylance can be told to [ignore a particular line/file](https://www.reddit.com/r/VisualStudioCode/comments/i3mpct/comment/g5bkx9u/) 
    * add `type: ignore` as a comment either at the end of the line or the top of the file.
    * useful for when a script calls microcontroller imports that aren't part of the dev system.