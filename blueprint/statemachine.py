from .utility import check_if_microcontroller
from .messages import MessageBuffer

class StateMachine:

    def __init__(self, init_state = 'Initialize', final_state = 'Shutdown'):
        self.state = None
        self.states = {}
        self.counter = 0
        self.running = False
        self.properties = {}
        self.messages = MessageBuffer() # Not needed yet - might be work using this instead of in sdl_communicator
        self.is_microcontroller = check_if_microcontroller()
        self.init_state = init_state
        self.final_state = final_state

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            print(f'Exiting {self.state.name}.')
            self.state.exit(self)
        self.state = self.states[state_name]
        print(f'Entering {self.state.name}.')
        self.state.enter(self)

    def update(self):
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            #print(f'Updating {self.state.name}')
            self.state.update(self)

    def run(self, state_name = None):
        self.running = True
        if state_name is None:
            self.go_to_state(self.init_state)
        else:
            self.go_to_state(state_name)

    def stop(self):
        self.running = False


class State:
    def __init__(self):
        self.entered_at = 0
        self.counter = 0
        self.properties = {}

    @property
    def name(self):
        return ''

    def enter(self, machine):
        pass

    def exit(self, machine):
        pass

    def update(self, machine):
        pass



