# type: ignore
from mse0.sdl_communicator import sdlCommunicator
from mse0.messages import make_message, parse_payload
from mse0.utility import check_key_and_type
import time
import neopixel
import board
import digitalio
import random

class sdlTest:
    '''
    A test subsystem that should work on a variety of microcontrollers
    - recieves a command to blink the builtin led
    - can change the color of the neopixel (if available)
    - uses a random function to simulate a notification or alert routine
    '''

    # Functions registered in the commands dictionary must be defined before __init__
    
    def blink_function(self, **kwargs):
        """
        blink the builtin led
        """
        try:
            num = int(kwargs["num"])
        except:
            print("using default number of blinks")
            num = 5
        try:
            delay = float(kwargs['delay'])
        except:
            print("using default delay")
            delay = 0.5
        for i in range(num):
            self.led.value = True
            time.sleep(delay)
            self.led.value = False
            time.sleep(delay)
        
        message = make_message(
            self.name,"RESPONSE", "SUCCESS", 
            f"Blinking has completed")
        print(message)    
        return message    

    def color_function(self, **kwargs):
        """ 
        Updates the color of the neopixel LED
        """
        red = 0
        green = 0
        blue = 0
        if check_key_and_type(kwargs, "red",int):
            red = kwargs["red"]
        if check_key_and_type(kwargs, "green",int):
            green = kwargs["green"]
        if check_key_and_type(kwargs, "blue",int):
            blue = kwargs["blue"]
        
        self.neopixel[0] = (red, green, blue)
        time.sleep(1)
        message = make_message(
            self.name,"RESPONSE", "SUCCESS", 
            f"Color updated to {self.neopixel[0]}")
        print(message)
        return(message)
        
    def __init__(self):
        self.name = "Test"
        self.version = "0.1"
        self.description = "Subsystem testing functionality and serving as a template"
        self.communicator = sdlCommunicator(self.name)
        self.commands = {
            "blink": self.blink_function,
            "color": self.color_function,
        }

        self.led = digitalio.DigitalInOut(board.LED)
        self.led.direction = digitalio.Direction.OUTPUT
        self.neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness = 0.1)

    # Chores - These are functions that would not be requested, but are performed by the microcontroller
    def check_for_errors(self):
        """
        A test function that will report an error 0.1 % of the time.
        The value is low because we are polling, and therefore this function will execute many times.
        """
        message = None
        num = random.random()
        if num < 0:
            message = make_message(
                self.name,"ALERT", "SUCCESS", 
                f"A warning has been raised.",
                jsonq = False)
        # Send message to the outbox
        if message is not None:
            self.communicator.writebuffer.store_message(message)
            print(message)
        return message

        
    def run(self, loglevel = 1):
        """
        poll for commands
        check for errors
        send information based upon log level
        """
        self.loglevel = loglevel # Reserved for future use
        while True:
            # Check the inbox
            self.communicator.read_serial_data()
            # Do requested tasks
            if not self.communicator.readbuffer.is_empty():
                message = self.communicator.readbuffer.get_oldest_message(jsonq=False)
                payload = parse_payload(message['payload'])
                return_message = self.execute_command(payload)
                self.communicator.writebuffer.store_json(return_message)
            # Do chores
            self.check_for_errors()
            # Empty the outbox
            self.communicator.write_serial_data()
            
            time.sleep(2)
            

    
    def execute_command(self, command):
        if command['func'] in self.commands:
            message = self.commands[command['func']](**command)
        else:
            message = make_message(
                self.name,"ALERT", "FAILED", "Command was not understood")
        return message
    


