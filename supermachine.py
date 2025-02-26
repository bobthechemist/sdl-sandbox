from blueprint.statemachine import State, StateMachine
import blueprint.subsystems.pumpdemo as ps
from time import monotonic, sleep

# Create a pump
pump1 = StateMachine(init_state='Idle', name='Pump 1')
pump1.add_flag('start',False)
pump1.add_state(ps.Idle())
pump1.add_state(ps.Aspirate())
pump1.add_state(ps.Dispense())
pump1.run()

# Create another pump
pump2 = StateMachine(init_state='Idle', name='Pump 2')
pump2.add_flag('start',False)
pump2.add_state(ps.Idle())
pump2.add_state(ps.Aspirate())
pump2.add_state(ps.Dispense())
pump2.run()

start_time = monotonic()
pump1.flags['start'] = True
pump2.flags['start'] = False
while monotonic() - start_time < 30:
    pump1.update()
    pump2.update()
    if monotonic() - start_time > 9:
        pump2.flags['start'] = True