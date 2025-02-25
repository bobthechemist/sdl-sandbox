# type: ignore
from blueprint.statemachine import State, StateMachine
from blueprint.communicator import Communicator
from blueprint.messages import make_message, parse_payload
from blueprint.utility import check_key_and_type
from time import sleep, monotonic
import board
import digitalio

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
        machine.pump_pin = digitalio.DigitalInOut(board.GP27)
        machine.pump_pin.direction = digitalio.Direction.OUTPUT
        machine.pump_pin.value = False # Make sure pump is in dispense mode
        machine.aspriate_time = 0.1 # May be different for different model pumps
        machine.volume = 10 # volume of pump in microliters
        machine.serial = Communicator(subsystem_name='SIDEKICK')
        print('Initialization completed')
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
        print("Pump in listening state")

    def enter(self, machine):
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
                if cmd['func'] is 'dispense':
                    # Argument is the volume in microliters
                    machine.target_volume = cmd['arg1'] # Better argument handling will be needed 
                    machine.num_cycles = int(machine.target_volume / machine.volume) # always rounds down
                    machine.go_to_state("Aspirate")


    def exit(self, machine):
        pass

class Aspirate(State):
    def __init__(self):
        super().__init__()
    
    @property
    def name(self):
        return 'Aspirate'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        print("Starting Aspirate")
        machine.pump_pin.value = True # Sets the pump pin high
    
    def update(self, machine):
        elapsed_time = monotonic() - self.entered_at
        if elapsed_time >= machine.aspirate_time:
            machine.go_to_state('Dispense')