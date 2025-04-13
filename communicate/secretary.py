import time
from .statemachine import StateMachine, State

# Assuming you have MessageBuffer, Postman, and other relevant classes
class SecretaryStateMachine(StateMachine):
    """
    A state machine to manage message processing and routing.
    """

    def __init__(self, inbox, outbox, subsystem_router, filer=None, postman = None, name = "secretary"):
        """Initializes the SecretaryStateMachine."""
        super().__init__(init_state='Monitoring', name=name)  # set the name for the logging

        self.inbox = inbox
        self.outbox = outbox
        self.subsystem_router = subsystem_router
        self.filer = filer
        self.postman = postman
        #Add states
        self.add_state(Monitoring())
        self.add_state(Reading())
        self.add_state(Filing())
        self.add_state(Error())

class Monitoring(State):
    """
    Secretary state of monitoring the inbox and outbox.
    If either one is populated, do something about it.
    Prefers sending messages
    """
    @property
    def name(self):
        return 'Monitoring'
    
    def enter(self, machine):
        machine.log.info("Monitoring")

    def update(self, machine):
        """
        Checks outbox and calls postman if necessary. Then checks the inbox 
        for new messages and transitions to ProcessMessage.
        """
        if not machine.outbox.is_empty():
            machine.log.info("Something to send, calling the postman")
            # Does mailing require its own state? It is just one line?
            #machine.go_to_state('Mailing')
            mail = machine.outbox.get()
            machine.postman.send(mail)
        else:
            message = machine.inbox.get()
            if message:
                machine.flags["current_message"] = message #Sets the current message to be used in other functions
                machine.log.info("New message, starting processing")
                machine.go_to_state('Reading')


class Reading(State):
    """
    Secretary state of reading a message from the inbox and deciding what to do
    Upon entering, create flags to decide if message should be filed, routed, or mailed. 
    Then, only exit state if all three are false.
    """
    @property
    def name(self):
        return 'Reading'

    def enter(self, machine):
        machine.log.debug("Reading a message")


    def update(self, machine):
        message = machine.flags["current_message"]
        # Determine actions to take based on the message (e.g., based on message.status, message.meta, etc.)
        # Example actions (you can customize these based on your needs):
        if self.should_route_to_subsystem(message, machine):
            machine.subsystem_router.route(message)
        if self.should_send_to_outbox(message, machine):
            machine.outbox.store(message)
        if self.should_file_message(message, machine):
            machine.go_to_state("Filing")
        else:
            machine.go_to_state("Monitoring")


    def should_file_message(self, message, machine):
      #Add your logic to determine if the message should be filed or not.
      #For testing always file the message
      machine.log.debug("checking to file - will do it")
      return True
    
    def should_route_to_subsystem(self, message, machine):
      #Add your logic to determine if the message should be sent to a subsystem
      #For testing always send the message
      machine.log.debug("checking to route - won't do it")
      return False
    
    def should_send_to_outbox(self, message, machine):
      #Add your logic to determine if the message should be sent to the outbox
      #For testing always send the message
      machine.log.debug("checking to send to outbox - will do it")
      return True

class Filing(State):
    """Filing class reads the message and processes the message to complete the goal of the subsystem"""
    @property
    def name(self):
        return 'Filing'

    def enter(self, machine):
        machine.log.info("Filing the message")

    def update(self, machine):
        if machine.filer:
            message = machine.flags["current_message"]
            machine.filer.file_message(message)  # Assumes the filer provides store_message
            #machine.flags["current_message"] = None #Remove the old value
            machine.flags['file'] = False # Done filing - do this in exit?
        else:
            machine.log.warning("There is no filing system to store")
        machine.go_to_state('Reading')

class Error(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Error'

    def enter(self, machine):
        machine.log.critical("error")
        machine.log.critical(machine.flags["error_message"])

    def update(self, machine):
        time.sleep(10)
        machine.log.warning("Going back to idling")
        machine.go_to_state("Monitoring")

class SubsystemRouter:  # Place holder for the logic on how the system routes messages
    def route(self, message):
        # Add code here that routes messages to the right subsytem
        pass  # Example, subsystems may be "engine", "brakes", "lights"

class Outbox:
    def add_message(self, message):
        # Place holder to do code for adding a message to a subsystem. This function should never call Postman
        pass

class Filer():
    """
    Base class for filing messages
    """

    def __init__(self, param = {}):
        """
        Initilize the filing system
        """
        self.parameters = param # Implementation specific parameter set

    def file_message(self, msg = None):
        """
        Files message
        """
        if msg:
            self._file_message(msg) # Implemenation specific filing
        else:
            pass
    
    def _file_message(self, msg):
        """files message, implementation specific"""
        raise NotImplementedError("Implementation specific filing not implemented")

class CircularFiler(Filer):
    """
    Prints message to console unless print parameter is False
    """

    def __init__(self, param = {'print': True}):
        super().__init__(param)
        

    def _file_message(self, msg):
        if self.parameters['print']:
            print(msg)
        else:
            print('nom nom nom')

"""
# Create instances of the necessary components
inbox = LinearMessageBuffer()
outbox = LinearMessageBuffer()
subsystem_router = SubsystemRouter()

# Create a filer (e.g., a database logger) - replace with your actual filer implementation
class DatabaseFiler:
    def store_message(self, message):
        print(f"Filing message to database: {message}")

filer = DatabaseFiler()
postman = Postman({"protocol":"serial"})

# Instantiate the SecretaryStateMachine
secretary = SecretaryStateMachine(inbox=inbox, outbox=outbox, subsystem_router=subsystem_router, filer=filer, postman = postman)

# Add some messages to the inbox
inbox.store({"message_type": "DATA", "data": "Some sensor data"})
inbox.store({"message_type": "COMMAND", "command": "Start engine"})

# Start the state machine
secretary.run()

print('done')
# (Later, to stop the state machine)
# secretary.stop()
"""