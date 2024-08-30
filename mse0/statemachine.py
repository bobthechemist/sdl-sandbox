from time import monotonic

class StateMachine:

    def __init__(self):
        self.state = None
        self.states = {}
        self.counter = 0
        self.running = False
        self.properties = {}

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            print(f'Exiting {self.state.name}.')
            self.state.exit(self)
        self.state = self.states[state_name]
        print(f'Entering {self.state.name}')
        self.state.enter(self)
    
    def update(self):
        if self.state:
            #print(f'Updating {self.state.name}')
            self.state.update(self)
    
    def run(self, state_name):
        self.running = True
        self.go_to_state(state_name)
    
    def stop(self):
        self.running = False
    

class State:
    def __init__(self):
        self.entered_at = 0
        self.counter = 0

    @property
    def name(self):
        return ''
    
    def enter(self, machine):
        pass

    def exit(self, machine):
        pass

    def update(self, machine):
        pass