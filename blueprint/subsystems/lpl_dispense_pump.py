# type: ignore
from blueprint.statemachine import State
from time import monotonic


'''
States for the LPL series dispense pumps from LEE

When the Sidekick was published, they provided a 10 uL pump (LPMX0501600B) which
is no longer available. There are 25 uL and 50 uL pumps on the website (LPLA1250650L and
LPLA1250625L) which work the same way but with different timing.

The LMPX series required 0.1 s aspirate and 0.1+ dispense (5 hz max). The LPLA series requires
a 2 hz max rate (0.250 s aspirate, 0.250+ dispense).

See https://www.theleeco.com/product/lpl-series-fixed-volume-dispense-pump/#

The state machine will need to provide
.num_cycles: number of times to dispense liquid
.aspirate_time: time that the actuation voltage is applied
.dispense_time: minimum time to keep voltage low
.control_pin: the digitialio object corresponding to the pump
'''


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
        machine.control_pin.value = True
        if machine.num_cycles <= 0:
            print(f'{machine.name} is not sure how we got here.')

    def update(self, machine ):
        delta = monotonic() - self.entered_at
        if delta > machine.aspirate_time:
            machine.go_to_state('Dispense')

    def exit(self, machine):
        super().exit(machine)
        machine.control_pin.value = False

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





