# type: ignore
from blueprint.statemachine import StateMachine
from blueprint.communicator import Communicator
from blueprint.messages import parse_payload
import blueprint.subsystems.lpl_dispense_pump as ps # Get pump states
from time import sleep, monotonic
import board
import digitalio



# Think of Sidekick as a container of state machines. After we learn what we want a container to do, it should be possible to create a container class.

'''
Does the container need to be a state machine?

It needs to listen for available instructions and update the state machines it contains
Sounds to me like this is a microcontroller setup/loop style

Example uC code:

from blueprint.subsystems.sidekick import Sidekick
from time import monotonic, sleep


machine = Sidekick(num_pumps=4,
    pins=["GP27","GP26","GP22","GP21"],
    a_times=[0.1,0.1,0.1,0.1],
    d_times=[0.2,0.25,0.3,0.35])

machine.run()
machine.start_pump([0,1,2,3])

while True:
    machine.loop()


on the host side:

from blueprint.host_utilities import find_data_comports
from blueprint import communicator
from blueprint.messages import make_message

ports = find_data_comports()
subs = [communicator.Communicator(port= p['port']) for p in ports]
msg = make_message(comm_type='REQUEST',payload="dispense 0 500")
subs[0].writebuffer.store_message(msg)
subs[0].write_serial_data()
def d(pump, volume):
    msg = make_message(comm_type='REQUEST', payload=f'dispense {pump} {volume}')
    subs[0].writebuffer.store_message(msg)
    subs[0].write_serial_data()

out = [d(i,1000) for i in range(4)]
'''
class Sidekick:
    def __init__(self, num_pumps=1, pins=None, a_times=None, d_times=None):
        self.default_a_time = 0.1
        self.default_d_time = 0.2
        if pins is None:
            raise ValueError("Pins must be set")
        if a_times is None:
            a_times = [self.default_a_time] * num_pumps
        if d_times is None:
            d_times = [self.default_d_time] * num_pumps
        if len(a_times) != num_pumps or len(d_times) != num_pumps:
            raise ValueError("Length of a_times and d_times must match num_pumps")
        self.pumps = [
            self.create_pump(name=f'pump{i}', pin=pins[i], a_time=a_times[i], d_time=d_times[i])
            for i in range(num_pumps)
        ]
        self.serial = Communicator(subsystem_name='SIDEKICK')

    def create_pump(self, name="pump", pin=None, a_time=None, d_time=None):
        if a_time is None:
            a_time = self.default_a_time
        if d_time is None:
            d_time = self.default_d_time
        if pin is None:
            raise ValueError("Pins must be set - shouldn't have gotten here.")

        pump = StateMachine(init_state='Idle', name=name)
        pump.add_flag('start', False)
        pump.aspirate_time = a_time
        pump.dispense_time = d_time if d_time > a_time else a_time
        pump.num_cycles = 0
        try:
            p = getattr(board,pin)
            pump.control_pin = digitalio.DigitalInOut(p)
            pump.control_pin.direction = digitalio.Direction.OUTPUT
        except AttributeError:
            raise ValueError(f"{pin} does not seem to be a valid pin")
        pump.add_state(ps.Idle())
        pump.add_state(ps.Aspirate())
        pump.add_state(ps.Dispense())

        return pump

    def start_pump(self, pump_numbers):
        self._set_pump_flags([pump_numbers] if isinstance(pump_numbers,int) else pump_numbers,
            'start', True)

    def stop_pump(self, pump_numbers):
        self._set_pump_flags([pump_numbers] if isinstance(pump_numbers,int) else pump_numbers,
            'start', False)

    def _set_pump_flags(self, pump_numbers, flag_name, flag_value):
        if not isinstance(pump_numbers, list):
            raise ValueError("Pump numbers must be provided as a list")

        for pump_num in pump_numbers:
            if not isinstance(pump_num, int):
                raise ValueError("Invalid pump number")
            if pump_num < 0 or pump_num >= len(self.pumps):
                raise ValueError(f"Invalid pump number: {pump_num}")

            self.pumps[pump_num].add_flag(flag_name, flag_value)

    def set_num_cycles(self, pump_num, num_cycles):
        if not isinstance(pump_num, int) or not isinstance(num_cycles, int):
            raise ValueError("Pump number and num_cycles must be integers")
        if pump_num < 0 or pump_num >= len(self.pumps):
            raise ValueError(f"Invalid pump number: {pump_num}")
        self.pumps[pump_num].num_cycles = num_cycles


    # Container functions loop the statemachine function across all state machines in the container
    def run(self):
        for p in self.pumps:
            p.run()

    def stop(self):
        for p in self.pumps:
            p.stop()

    def update(self):
        for p in self.pumps:
            p.update()

    # Communication tools
    '''
    dispense <pump number> <volume in microliters>
    '''
    def loop(self):
        self.update()
        self.serial.read_serial_data()
        if not self.serial.readbuffer.is_empty():
            msg = self.serial.readbuffer.get_oldest_message(jsonq=False)
            print(msg)

            # Process the message if it is a REQUEST
            if msg['comm_type'] is 'REQUEST':
                print('Performing operation')
                cmd = parse_payload(msg['payload'])
                if cmd['func'] is 'dispense':
                    # assuming proper formatting
                    p = int(cmd['arg1'])
                    v = int(float(cmd['arg2'])/10.)
                    self.set_num_cycles(p,v)
        if not self.serial.writebuffer.is_empty():
            pass
        sleep(0.001)

