# type: ignore
from mse0.statemachine import State, StateMachine
from mse0.messages import make_message, parse_payload
from mse0.host_utilities import find_data_comports
from time import monotonic

#States
#Listening, Initializing, Reacting, Error, Responding, Shutdown
#Some of these might be the same (Listening, Responding)

class Initialize(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Initialize'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        data = find_data_comports()
        if len(data) < 1:
            machine.properties['error_message'] = "Problem with com ports"
            machine.go_to_state('Error')

    def update(self, machine):
        print("finished doing startup stuff")
        machine.go_to_state("State 1")

class Error(State):
    def __init__(self):
        super().__init__()
    
    @property
    def name(self):
        return 'Error'
    
    def enter(self, machine):
        print(f'ERROR MESSAGE: {machine.properties["error_message"]}')
        machine.go_to_state('Shutdown')
        # Will need to go somewhere


class OneState(State):
    def __init__(self):
        super().__init__()
        

    @property
    def name(self):
        return 'State 1'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        print(f'entered at {self.entered_at}.')
        machine.counter = machine.counter + 1

    
    def update(self, machine):
        if monotonic() - self.entered_at > 2:
            machine.go_to_state('State 2')
        if machine.counter >= 2:
            print(f'counter is {machine.counter} which is different from {self.counter}')
            machine.go_to_state('Shutdown')
    

class TwoState(State):
    def __init__(self):
        super().__init__()
        

    @property
    def name(self):
        return 'State 2'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        machine.counter = machine.counter + 1

    def update(self, machine):
        if monotonic() - self.entered_at > 2:
            machine.go_to_state('State 1')
        if machine.counter >= 2:
            print(f'counter is {machine.counter} which is different from {self.counter}')
            machine.running = False
        
    
class Shutdown(State):
    def __init__(self):
        super().__init__()
        

    @property
    def name(self):
        return 'Shutdown'    

    def enter(self, machine):
        print('we are done')
        machine.stop()

# Create the state machine. `machine` should be the name of the subsystem
machine = StateMachine()
# Add the states that have been created
machine.add_state(Initialize())
machine.add_state(Error())
machine.add_state(OneState())
machine.add_state(TwoState())
machine.add_state(Shutdown())
# Set the initial state - will let user do this.
# machine.go_to_state('Initialize')
# Code that user will run to get the subsystem going
'''
machine.run()
while machine.running:
    machine.update()
'''