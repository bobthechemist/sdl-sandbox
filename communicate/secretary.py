import time
from message import Message
from message_buffer import LinearMessageBuffer
from postman import Postman
from statemachine import StateMachine, State

# Assuming you have MessageBuffer, Postman, and other relevant classes
class SecretaryStateMachine(StateMachine):
    """
    A state machine to manage message processing and routing.
    """

    def __init__(self, inbox, outbox, subsystem_router, filer=None, postman = None, name = "secretary"):
        """Initializes the SecretaryStateMachine."""
        super().__init__(init_state='Idle', name=name)  # set the name for the logging

        self.inbox = inbox
        self.outbox = outbox
        self.subsystem_router = subsystem_router
        self.filer = filer
        self.postman = postman
        #Add states
        self.add_state(Idle())
        self.add_state(ProcessMessage())
        self.add_state(FileMessage())
        self.add_state(Error())

class Idle(State):
    @property
    def name(self):
        return 'Idle'
    
    def enter(self, machine):
        machine.log.info("idling")

    def update(self, machine):
        """Checks the inbox for new messages and transitions to ProcessMessage."""
        # Check if outbox is not empty and if so, call the postman.
        mail = machine.outbox.get()
        if mail:
            self.postman.send(mail)
        message = machine.inbox.get()
        if message:
            machine.flags["current_message"] = message #Sets the current message to be used in other functions
            machine.log.info("New message, starting processing")
            machine.go_to_state('ProcessMessage')

class ProcessMessage(State):
    @property
    def name(self):
        return 'ProcessMessage'

    def enter(self, machine):
        machine.log.info("Processing a message")

    def update(self, machine):
      message = machine.flags["current_message"]
      # Determine actions to take based on the message (e.g., based on message.status, message.meta, etc.)
      # Example actions (you can customize these based on your needs):
      try: # Wrap the actions in a try block, so that the state can be transitioned if fails
        if self.should_file_message(message, machine): #pass the machine to the helper as well
            machine.go_to_state("FileMessage")

        if self.should_route_to_subsystem(message, machine):
            machine.subsystem_router.route(message)

        if self.should_send_to_outbox(message, machine):
            machine.outbox.add_message(message)
      except Exception as e:
        print(f"ERROR MESSAGE: {e}")
        machine.flags["error_message"] = e
        machine.log.critical(f"The following error has occured{e}")
        machine.go_to_state("Error")
      finally:
        machine.go_to_state("Idle")

    def should_file_message(self, message, machine):
      #Add your logic to determine if the message should be filed or not.
      #For testing always file the message
      machine.log.debug("checking to file")
      return True
    
    def should_route_to_subsystem(self, message, machine):
      #Add your logic to determine if the message should be sent to a subsystem
      #For testing always send the message
      machine.log.debug("checking to route")
      return True
    
    def should_send_to_outbox(self, message, machine):
      #Add your logic to determine if the message should be sent to the outbox
      #For testing always send the message
      machine.log.debug("checking to send to outbox")
      return True

class FileMessage(State):
    """Filing class reads the message and processes the message to complete the goal of the subsystem"""
    @property
    def name(self):
        return 'FileMessage'

    def enter(self, machine):
        machine.log.info("Storing in the filer")

    def update(self, machine):
        if machine.filer:
            message = machine.flags["current_message"]
            machine.filer.store_message(message)  # Assumes the filer provides store_message
            machine.flags["current_message"] = None #Remove the old value
        else:
            machine.log.warning("There is no filing system to store")
        #Transition to the next state

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
        machine.go_to_state("Idle")

class SubsystemRouter:  # Place holder for the logic on how the system routes messages
    def route(self, message):
        # Add code here that routes messages to the right subsytem
        pass  # Example, subsystems may be "engine", "brakes", "lights"

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