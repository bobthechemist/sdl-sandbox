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

