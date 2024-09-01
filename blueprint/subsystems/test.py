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
        machine.serial = sdlCommunicator(subsystem_name='TEST')
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

class ListeningTest(State):
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

class Listening(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Listening'

    def enter(self, machine):
        self.entered_at = monotonic()

    def update(self, machine):
        # Check for messages
        machine.serial.read_serial_data()
        if not machine.serial.readbuffer.is_empty():
            msg = machine.serial.readbuffer.get_oldest_message(jsonq=False)
            print(msg)
            # process the message if it is a REQUEST
            if msg['comm_type'] is 'REQUEST':
                print("Performing operation")
                # May have a request processing state that looks at function and decides what to do.
                cmd = parse_payload(msg['payload'])
                if cmd['func'] is 'blink':
                    print('will blink')
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

class ReceiveTest(State):
    '''
    Special class to test if a microcontroller can receive serial commands
    '''
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'ReceiveTest'

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
        machine.properties['neopixel'][:] = (255,255,0)
        machine.serial = sdlCommunicator(subsystem_name = 'TEST')
        print('Initialization completed.')




    def update(self, machine):
        machine.serial.read_serial_data()
        if not machine.serial.readbuffer.is_empty():
            msg = machine.serial.readbuffer.get_oldest_message(jsonq=False)

            print(msg)
            print(msg['payload'])
            print(parse_payload(msg['payload']))





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
machine.add_state(ReceiveTest())




