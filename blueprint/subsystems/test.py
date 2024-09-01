# type: ignore
from blueprint.statemachine import State, StateMachine
from blueprint.sdl_communicator import sdlCommunicator
from blueprint.messages import make_message, parse_payload
from blueprint.utility import check_key_and_type
from time import sleep, monotonic
import neopixel
import board
import digitalio
import random


### FSM approach
class Initialize(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Initialize'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        if not machine.is_microcontroller:
            machine.properties['error_message'] = "This subsystem must be run on a microcontroller"
            machine.go_to_state('Error')
        # Set machine properties, in this case the red LED and neopixel
        machine.properties['led'] = digitalio.DigitalInOut(board.LED)
        machine.properties['led'].direction = digitalio.Direction.OUTPUT
        machine.properties['led'].value = False
        machine.properties['blinking'] = False
        machine.properties['neopixel'] = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness = 0.01)
        machine.properties['neopixel'][:] = (0,0,0)
        
        print('Initialization completed.')
        machine.go_to_state('Listening')
        
        
    def update(self, machine):
        pass
    
    def exit(self, machine):
        pass

class Error(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Error'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        print(f'ERROR MESSAGE: {machine.properties["error_message"]}')
        machine.go_to_state(machine.final_state)
    
    def update(self, machine):
        pass
    
    def exit(self, machine):
        pass

class Listening(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Listening'
    
    def enter(self, machine):
        self.entered_at = monotonic()
    
    def update(self, machine):
        # Simulate receiving a command to change colors
        if random.random() < 0.001:
            machine.properties['colors'] =  [(0,0,0), (255, 0, 0), (255,255,0), (0, 255, 0), (0,255,255), (0, 0, 255),(255,0,255), (255,255,255)]
            machine.properties['color'] = random.choice(machine.properties['colors'])
            print(f'Simulated command received. Changing color to {machine.properties["color"]}')
            machine.go_to_state('Colorchange')
        # Simulate receiving a command to blink
        if random.random() < 0.002:
            print(f'Simulated command received. Preparing to blink')
            machine.go_to_state('Blink')
        # If we are blinking, need to update that state
        if machine.properties['blinking']:
            machine.go_to_state('Blink')
            
    def exit(self, machine):
        pass

class Sending(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Sending'
    
    def enter(self, machine):
        self.entered_at = monotonic()
    
    def update(self, machine):
        pass
    
    def exit(self, machine):
        pass

class Reacting(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Reacting'
    
    def enter(self, machine):
        self.entered_at = monotonic()

    
    def update(self, machine):
        pass
    
    def exit(self, machine):
        pass

class Shutdown(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Shutdown'
    
    def enter(self, machine):
        self.entered_at = monotonic()
    
    def update(self, machine):
        pass
    
    def exit(self, machine):
        pass

class Colorchange(State):
    def __init__(self):
        super().__init__()
    
    @property 
    def name(self):
        return 'Colorchange'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        machine.properties['neopixel'][0] = machine.properties['color']
        machine.go_to_state('Listening')

class Blink(State):
    def __init__(self):
        super().__init__()
    
    @property
    def name(self):
        return 'Blink'
    
    def enter(self, machine):
        if machine.properties['blinking'] is False:
            # First time entering so set initial parameters 
            machine.properties['blinking'] = True
            machine.properties['led'].value = True
            self.blink_delay = 0.1
            self.blink_count = 10
            self.counter = 0
            self.entered_at = monotonic()
        else:
            # Will do the update here to avoid having to enter blink twice
            if monotonic() - self.entered_at > self.blink_delay:
                machine.properties['led'].value = not machine.properties['led'].value
                self.counter = self.counter + 1
                self.entered_at = monotonic()
            if self.counter > self.blink_count:
                # Done blinking
                machine.properties['led'].value = False
                machine.properties['blinking'] = False
        machine.go_to_state('Listening')
    
# Create the state machine. `machine` should be the name of the subsystem
machine = StateMachine()
# Add the states that have been created
machine.add_state(Initialize())
machine.add_state(Error())
machine.add_state(Listening())
machine.add_state(Reacting())
machine.add_state(Sending())
machine.add_state(Shutdown())
machine.add_state(Colorchange())
machine.add_state(Blink())
### OLD code to be deprecated
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
    


