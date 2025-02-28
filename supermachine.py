from blueprint.subsystems.sidekick import Sidekick
from time import monotonic, sleep
import sys

machine = Sidekick(num_pumps=2,a_times=[0.1,0.1],d_times=[0.2,0.4])
machine.set_num_cycles(0,3)
machine.set_num_cycles(1,5)
machine.run()
machine.start_pump(0)
start_time = monotonic()
do_this = True
while monotonic() - start_time < 30:
    machine.update()
    if monotonic() - start_time > 9 and do_this:
        machine.start_pump(1)
        do_this = False



sys.exit()

# Create a pump
pump1 = StateMachine(init_state='Idle', name='Pump 1')
pump1.add_flag('start',False)
pump1.aspirate_time =  0.5 # The aspirate or energize time for the pump
pump1.dispense_time = 1 # Cannot be less than aspirate_time. Pumps require 50% duty cycle
pump1.num_cycles = 1 # Adjust this to deliver liquid
pump1.add_state(ps.Idle())
pump1.add_state(ps.Aspirate())
pump1.add_state(ps.Dispense())
pump1.run()

# Create another pump
pump2 = StateMachine(init_state='Idle', name='Pump 2')
pump2.add_flag('start',False)
pump2.aspirate_time =  3 # The aspirate or energize time for the pump
pump2.dispense_time = 3 # Cannot be less than aspirate_time. Pumps require 50% duty cycle
pump2.add_state(ps.Idle())
pump2.add_state(ps.Aspirate())
pump2.add_state(ps.Dispense())
pump2.run()

start_time = monotonic()
pump1.flags['start'] = True
pump2.flags['start'] = False
do_this = True
while monotonic() - start_time < 30:
    pump1.update()
    #pump2.update()
    if monotonic() - start_time > 9 and do_this:
    #    pump2.flags['start'] = True
        pump1.num_cycles = 4
        do_this = False