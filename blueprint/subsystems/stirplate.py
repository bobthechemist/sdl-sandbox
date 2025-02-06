# type: ignore
from blueprint.statemachine import State, StateMachine
from blueprint.communicator import Communicator
from blueprint.messages import make_message, parse_payload
from blueprint.utility import check_key_and_type
from time import sleep, monotonic
import board
import digitalio

# import pwmio # Won't use due to minimum frequency
# import pulseio # Not implemented yet


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
        machine.pwm = digitalio.DigitalInOut(board.D10)
        machine.pwm.direction = digitalio.Direction.OUTPUT
        machine.duty_cycle = 0 # Initial duty cycle
        machine.period = 1 # Initialize the period
        machine.start = True # Start the stirring (even if it is set to duty_cycle 0)
        machine.serial = Communicator(subsystem_name='STIRPLATE')
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
                print(cmd)
                if cmd['func'] is 'low':
                    machine.duty_cycle = 0.5
                    machine.period = 1
                elif cmd['func'] is 'high':
                    machine.duty_cycle = 1
                    machine.period = 1
                elif cmd['func'] is 'off':
                    machine.duty_cycle = 0
                    machine.period = 1


    def update(self, machine):
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
        #print(machine.active_command)
        if machine.start:
            machine.pwm.value = True
            machine.start = False
            machine.current_time = monotonic()
            machine.target_time = machine.duty_cycle * machine.period
        else:
            if machine.pwm.value: # The stirplate cycle is high
                if monotonic() - machine.current_time > machine.target_time:
                    machine.current_time = monotonic()
                    machine.target_time = (1-machine.duty_cycle)*machine.period
                    machine.pwm.value = False
            else: # The stirplate cycle is low
                if monotonic() - machine.current_time > machine.target_time:
                    machine.current_time = monotonic()
                    machine.target_time = machine.duty_cycle * machine.period
                    machine.pwm.value = True


    def update(self, machine):
        machine.go_to_state("Listening")

# Create the state machine. `machine` should be the name of the subsystem
machine = StateMachine()
# Add the states that have been created
machine.add_state(Initialize())
machine.add_state(Error())
machine.add_state(Listening())
machine.add_state(Stirring())
