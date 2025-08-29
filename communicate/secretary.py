import time
from shared_lib.statemachine import StateMachine, State

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
        machine.log.info("Monitoring for new tasks.")

    def update(self, machine):
        """
        Checks outbox and calls postman if necessary. Then checks the inbox 
        for new messages and transitions to ProcessMessage.
        """
        if not machine.outbox.is_empty():
            machine.log.info("Message in outbox. Calling the postman to send.")
            mail = machine.outbox.get()
            if mail:
                # Issue 2 FIX: Serialize the message object before sending.
                machine.postman.send(mail.serialize())
        else:
            message = machine.inbox.get()
            if message:
                machine.flags["current_message"] = message #Sets the current message to be used in other functions
                machine.log.info("New message received. Transitioning to Reading.")
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
        message = machine.flags.get("current_message")
        if message:
            # Log the dictionary representation for better readability
            machine.log.debug(f"Now reading message: {message.to_dict()}")
        else: 
            machine.log.warning("Entered Reading state with no message! Returning to Monitoring.")
            machine.go_to_state('Monitoring')


    def update(self, machine):
        # Issue 1 FIX: Get the message from the machine flags, not the inbox.
        message = machine.flags.get("current_message")

        if not message:
             # If there's no message, we shouldn't be here. Go back to monitoring.
             machine.log.warning("No message found in flags during Reading update. Returning to Monitoring.")
             machine.go_to_state('Monitoring')
             return # Exit the update function for this cycle

        # Determine actions to take based on the message object's properties
        if self.should_route_to_subsystem(message, machine):
            machine.log.debug(f"Routing message payload: {message.payload}")
            machine.subsystem_router.route(message)

        if self.should_send_to_outbox(message, machine):
            machine.log.debug(f"Mailing message payload: {message.payload}")
            machine.outbox.store(message)

        if self.should_file_message(message, machine):
            machine.log.debug(f"Filing message payload: {message.payload}")
            machine.go_to_state("Filing")
        else:
            # If not filing, the message is processed, so clear the flag and go back to monitoring.
            machine.flags["current_message"] = None
            machine.go_to_state("Monitoring")


    def should_file_message(self, message, machine):
      # Always file messages - if you don't want the messages, use the CircularFiler with 'print':False
      return True
    
    def should_route_to_subsystem(self, message, machine):
      # Route any message with the status "INSTRUCTION"
      machine.log.debug(f"Checking if message status '{message.status}' should be routed...")
      return message.status == "INSTRUCTION"
    
    def should_send_to_outbox(self, message, machine):
      # This logic is for the host-side secretary to echo things.
      # Responses should be generated by the subsystem router, so this is correctly False.
      return False



class Filing(State):
    """Filing class reads the message and processes the message to complete the goal of the subsystem"""
    @property
    def name(self):
        return 'Filing'

    def enter(self, machine):
        machine.log.info("Entering Filing state.")

    def update(self, machine):
        # Issue 1 FIX: Get the message from machine flags.
        message = machine.flags.get("current_message")
        if not message:
            machine.log.warning("No message in flags to file. Returning to Monitoring.")
            machine.go_to_state('Monitoring')
            return

        if machine.filer:
            machine.filer.file_message(message)
            machine.log.info("Message filed.")
        else:
            machine.log.warning("No filing system configured to store the message.")
        
        # After filing, we're done with this message. Clear the flag and go back to monitoring.
        machine.flags["current_message"] = None
        machine.go_to_state('Monitoring')

class Error(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Error'

    def enter(self, machine):
        machine.log.critical("An error has occurred in the Secretary.")
        error_msg = machine.flags.get("error_message", "No error message provided.")
        machine.log.critical(error_msg)

    def update(self, machine):
        time.sleep(10)
        machine.log.warning("Exiting error state and returning to Monitoring.")
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
            self._file_message(msg) # Implementation specific filing
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
            # Print the dictionary representation of the message for readability
            print(f"Filer: {msg.to_dict()}")
        else:
            # Silently "file" the message
            pass