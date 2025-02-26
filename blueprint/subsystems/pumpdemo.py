# type: ignore
from blueprint.statemachine import State
#from blueprint.communicator import Communicator
#from blueprint.messages import make_message, parse_payload
#from blueprint.utility import check_key_and_type
from time import monotonic
#import board
#import digitalio

class Idle(State):
    def _init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Idle'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        print(f'{machine.name} entered {self.name}')
    
    def update(self, machine ):
        if machine.flags['start']:
            machine.go_to_state('Aspirate')

class Aspirate(State):
    def _init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Aspirate'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        print(f'{machine.name} entered {self.name}')
    
    def update(self, machine ):
        delta = monotonic() - self.entered_at
        if delta > 2:
            machine.go_to_state('Dispense')

class Dispense(State):
    def _init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Dispense'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        print(f'{machine.name} entered {self.name}')
    
    def update(self, machine ):
        delta = monotonic() - self.entered_at
        if delta > 3:
            machine.go_to_state('Idle')



    

