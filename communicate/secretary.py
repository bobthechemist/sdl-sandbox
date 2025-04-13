import time
from .statemachine import StateMachine, State

'''
The secretary may need better task management. Right now it is very linear. Perhaps in a refactor reading a new message starts
with setting flags for what to do with the message (route, mail, file). Then there is a new state processing which cycles
through the other states. I cannot envision a situation when we need to go through secretary states more than once for a given
message. State machine might already be overkill.

For now: Monitor watches the inbox/outbox. If outbox gets populated, call the postman. If inbox is not empty, read. Reading
involves routing or mailing (not states, but probably will be in the future) and filing (a state). All of these should go back
reading because the message is processed multiple times. A flag of some sort informs secretary that everyone is done with the 
message, at which point it is removed from memory and we go back to monitoring.
'''


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
        message = machine.flags["current_message"]
        if message:
            machine.log.debug(f"Reading a message: {message}")
        else: 
            # My state machine logic currently goes back to Reading right after filing a message.
            machine.log.warning("No message! I shouldn't be here")
            machine.go_to_state('Monitoring')


    def update(self, machine):
        message = machine.flags["current_message"]
        # Determine actions to take based on the message (e.g., based on message.status, message.meta, etc.)
        # Example actions (you can customize these based on your needs):
        if self.should_route_to_subsystem(message, machine):
            machine.subsystem_router.route(message)
            machine.log.debug(f'routing {message["payload"]}')
        if self.should_send_to_outbox(message, machine):
            machine.outbox.store(message)
            machine.log.debug(f'mailing {message["payload"]}')
        if self.should_file_message(message, machine):
            machine.log.debug(f'filing {message["payload"]}')
            machine.go_to_state("Filing")
        else:
            machine.go_to_state("Monitoring")


    def should_file_message(self, message, machine):
      # Always file messages - if you don't want the messages, use the CircularFiler with 'print':False
      return True
    
    def should_route_to_subsystem(self, message, machine):
      #Add your logic to determine if the message should be sent to a subsystem
      #For testing always send the message
      machine.log.debug("I Route nothing, but will eventually route instructions")
      return False
    
    def should_send_to_outbox(self, message, machine):
      # For testing, only sending INFO. Might make sense for this to be the message_types above Instruction?

      return message["message_type"]=="INFO"



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
            machine.filer.file_message(message)  # Assumes the filer provides file_message
            machine.flags["current_message"] = None #Remove the old value
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

'''
Secretary may always have a technician to work with, but it is possible that technicians are part of the subsystems they control.
Alternatively, this might be technician logic. 
'''
class Router: 
    def route(self, message):
        # Add code here that routes messages to the right subsytem
        pass  # Example, subsystems may be "engine", "brakes", "lights"


'''
Secretary needs a way to file messages, so this class is a part of secretary.py
'''
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

