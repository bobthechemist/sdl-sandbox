# type: ignore
from blueprint.statemachine import State, StateMachine
from blueprint.sdl_communicator import sdlCommunicator
from blueprint.messages import make_message, parse_payload
from blueprint.utility import check_key_and_type
from time import sleep, monotonic
import board
import pwmio
import pulseio # Not implemented yet

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
        machine.tachometer_pin = board.A0
        machine.pwm_pin = pwmio.PWMOut(board.D12, frequency = 2)
        machine.LOWEST = 10000 # Lowest value to PWM the fan/stirplate
        machine.HIGHEST = 15000 # Highest practical value to PWM the fan/stirplate

        # Set machine properties, in this case the red LED and neopixel
        machine.serial = sdlCommunicator(subsystem_name='STIRPLATE')
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
                # Store the command for other states
                machine.active_command = cmd
                if cmd['func'] is 'stir':
                    print('will set stirring')
                    machine.go_to_state('Stirring')

    def exit(self, machine):
        pass

class Stirring(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Stirring'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        print(machine.active_command)
    
    def update(self, machine):
        if machine.active_command['arg1'] == 'high':
            machine.pwm_pin.duty_cycle = machine.HIGHEST
        elif machine.active_command['arg1'] == 'low':
            machine.pwm_pin.duty_cycle = machine.LOWEST
        elif machine.active_command['arg1'] == 'off':
            machine.pwm_pin.duty_cycle = 0
        else:
            print("did not understand command")
        machine.go_to_state("Listening")

# Create the state machine. `machine` should be the name of the subsystem
machine = StateMachine()
# Add the states that have been created
machine.add_state(Initialize())
machine.add_state(Error())
machine.add_state(Listening())
machine.add_state(Stirring())
