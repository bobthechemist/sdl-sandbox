# type: ignore
"""
Demonstration of a finite state machine. Runs on a microcontroller and accepts commands to blink the builtin LED and change the color of a neopixel.

Author(s): BoB LeSuer
"""
from blueprint.statemachine import State, StateMachine
from blueprint.communicator import Communicator
from blueprint.messages import make_message, parse_payload
import neopixel
import board
import digitalio
from time import monotonic

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
        machine.serial = Communicator(subsystem_name='DEMO')
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
            # Starting to blink, need to set timer and counter
            self.last_blinked_at = self.entered_at
            self.blink_counter = 0 # changes from on to off or off to on
            # hard coding the number of blinks
            self.number_of_blinks = 3
            self.blink_duration = 1 # for a *complete* blink
            self.blink_duty_cycle = 0.5 # fraction of duration in on state
            # Set initial state as on
            machine.led.value = True

    def update(self, machine):
        """
        Need to know current state to determine if the duration is duty_cycle * duration or (1- duty_cycle) * duration
        Need to know how many times the cycle has completed (starts on, so count transitions from off to on)
        """
        current_state = machine.led.value
        if current_state and (monotonic() - self.last_blinked_at) > self.blink_duty_cycle * self.blink_duration: # led is on and ready to transition
            machine.led.value = False
        if not current_state and (monotonic() - self.last_blinked_at) self.blink_duration: # should be done with blink cycle
            machine.led.value = True
            self.blink_counter = self.blink_counter + 1
        if self.blink_counter >= self.number_of_blinks: # blinking should be done now
            machine.flags['blink'] = False
            machine.led.value = False
            machine.go_to_state('Communicating')






# Create the state machine. `machine` should be the name of the subsystem
machine = StateMachine()
# Add the states that have been created
machine.add_state(Initialize())
machine.add_state(Communicating())
machine.add_state(Blinking())
machine.add_flag('blink', False)




