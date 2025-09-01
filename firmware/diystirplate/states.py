from shared_lib.statemachine import State
from shared_lib.messages import Message
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
        pass


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