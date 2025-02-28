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
        if machine.flags['start'] and machine.num_cycles > 0:
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
        if machine.num_cycles <= 0:
            print(f'{machine.name} is ')
    
    def update(self, machine ):
        delta = monotonic() - self.entered_at
        if delta > machine.aspirate_time:
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
        if delta > machine.dispense_time:
            # Done with the pump cycle, decide where to go based on num_cycles
            machine.num_cycles = machine.num_cycles - 1
            if machine.num_cycles > 0:
                machine.go_to_state('Aspirate')
            else:
                machine.go_to_state('Idle')



    

