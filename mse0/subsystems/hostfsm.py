# type: ignore
from mse0.statemachine import State, StateMachine
from mse0.messages import make_message, parse_payload
from mse0.host_utilities import find_data_comports
from mse0 import sdlCommunicator
from mse0.subsystems.directory import pid
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
        self.properties['setup_finished'] = False
        # Look for all USB ports that identify as Circuit Python
        machine.properties['ports'] = find_data_comports()
        if len(machine.properties['ports']) < 1:
            machine.properties['error_message'] = "Did not find any subsystems"
            machine.go_to_state('Error')
        # Establish a serial connection and read/write buffers for each subsystem found
        #   Also, identify each one using the PID and product directory
        else:
            machine.properties['subsystems'] =  [sdlCommunicator(port= p['port'], subsystem_name=pid[p['PID']]) for p in machine.properties['ports']]
            #for i in range(len(machine.properties['subsystems'])):
            #    machine.properties['subsystems'][i].subsystem_name = pid[machine.properties['ports'][i]['PID']]
            self.properties['setup_finished'] = True
        
        # Testing loops
        machine.properties['alreadysent'] = False

    def update(self, machine):
        if self.properties['setup_finished']:
            print("finished doing startup stuff")
            machine.go_to_state("Listening")

class Error(State):
    def __init__(self):
        super().__init__()
    
    @property
    def name(self):
        return 'Error'
    
    def enter(self, machine):
        print(f'ERROR MESSAGE: {machine.properties["error_message"]}')
        machine.go_to_state(machine.final_state)
        


class Listening(State):
    def __init__(self):
        super().__init__()
        

    @property
    def name(self):
        return 'Listening'
    
    def enter(self, machine):
        self.entered_at = monotonic()

    
    def update(self, machine):
        # Is there information in the buffers?
        for s in machine.properties['subsystems']:
            if s.serial.in_waiting > 0:
                s.read_serial_data()
            if not s.readbuffer.is_empty():
                print(s.readbuffer.get_oldest_message(jsonq = False))

        # Is there information from the user?
        if not machine.properties['alreadysent'] and monotonic() - self.entered_at > 5:
            machine.go_to_state('Sending')
        if monotonic() - self.entered_at > 10:
            print("I'm bored, shutting down")
            machine.go_to_state('Shutdown')
        
    


class Sending(State):
    def __init__(self):
        super().__init__()
        

    @property
    def name(self):
        return 'Sending'
    
    def enter(self, machine):
        self.entered_at = monotonic()
        msg = make_message("HOST", "REQUEST", "NA", "blink num=3 delay=1", jsonq=False)
        machine.properties['subsystems'][0].writebuffer.store_message(msg)
        machine.properties['subsystems'][0].write_serial_data()
        msg = make_message("HOST", "REQUEST", "NA", "blink num=10 delay=0.1", jsonq=False)
        machine.properties['subsystems'][1].writebuffer.store_message(msg)
        machine.properties['subsystems'][1].write_serial_data()
        machine.properties['alreadysent'] = True
        machine.go_to_state('Listening')


    def update(self, machine):
        pass
        

class Reacting(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Reacting'
    def enter(self, machine):
        self.entered_at = monotonic()


    def update(self, machine):
        pass

class Shutdown(State):
    def __init__(self):
        super().__init__()
        

    @property
    def name(self):
        return 'Shutdown'    

    def enter(self, machine):
        print('Closing all serial connections')
        [s.close() for s in machine.properties['subsystems']]
        machine.stop()

# Create the state machine. `machine` should be the name of the subsystem
machine = StateMachine()
# Add the states that have been created
machine.add_state(Initialize())
machine.add_state(Error())
machine.add_state(Listening())
machine.add_state(Reacting())
machine.add_state(Sending())
machine.add_state(Shutdown())
# Set the initial state - will let user do this.
# machine.go_to_state('Initialize')
# Code that user will run to get the subsystem going
'''
machine.run()
while machine.running:
    machine.update()
'''