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

    def update(self, machine):

        if not machine.is_microcontroller:
            machine.properties['error_message'] = "This subsystem must be run on a microcontroller"
            machine.go_to_state('Error')
        # Set machine properties, in this case the red LED and neopixel
        machine.led = digitalio.DigitalInOut(board.LED)
        machine.led.direction = digitalio.Direction.OUTPUT
        machine.led.value = False
        machine.blinking = False
        machine.neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness = 0.01)
        machine.neopixel[:] = (0,0,0)
        machine.serial = sdlCommunicator(subsystem_name='DEMO')
        print('Initialization completed.')
        machine.go_to_state('Communicating')

class Communicating(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Communicating'

    def enter(self, machine):
        super().enter(machine)

    def update(self, machine):
        # Check for messages
        machine.serial.read_serial_data()
        if not machine.serial.readbuffer.is_empty():
            msg = machine.serial.readbuffer.get_oldest_message(jsonq=False)
            print(msg)
            # process the message if it is a REQUEST
            if msg['comm_type'] is 'REQUEST':
                print("Performing operation")
                cmd = parse_payload(msg['payload'])
                machine.flags[cmd['func']] = True


        # Will treat states as linear
        machine.go_to_state('Blinking')
        
class Blinking(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Blinking'
    
    def enter(self, machine):
        super().enter(machine)
        if machine.flags['blink']:
            print("I blinked")
            machine.flags['blink'] = False
    
    def update(self, machine):
        machine.go_to_state('Communicating')





# Create the state machine. `machine` should be the name of the subsystem
machine = StateMachine()
# Add the states that have been created
machine.add_state(Initialize())
machine.add_state(Communicating())
machine.add_state(Blinking())




