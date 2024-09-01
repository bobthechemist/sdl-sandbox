# type: ignore
import time
#from adafruit_motorkit import Motorkit
from blueprint.sdl_communicator import sdlCommunicator
import blueprint.messages as messages

class sdlPumps:
    
    # Functions registered in the commands dictionary must be defined before __init__
    def throttle(self, **kwargs):
        """
        Keywords are pump and value. pump should be 1-4 and value -1 to 1
        """
        message = self.messages.create_json_message(
            self.name,"RESPONSE", "OK", 
            f"pump {kwargs['pump']} now set to {kwargs['value']}")
        print(message)
    def all_pumps_off(self):
        """ 
        turns all pumps off
        """
        message = self.messages.create_json_message(
            self.name,"RESPONSE", "OK", 
            f"All pumps set to 0 speed")
        print(message)
        
    def __init__(self):
        self.name = "Pumps"
        self.version = "0.1"
        self.description = "Subsystem for managing four peristaltic pumps"
        self.communicator = sdlCommunicator(self.name)
        self.messages = messages.MessageBuffer()
        self.commands = {
            "throttle": self.throttle,
            "off": self.all_pumps_off,
        }


        
    def run(self, loglevel = 1):
        """
        poll for commands
        check for errors
        send information based upon log level
        """
        self.loglevel = loglevel
        #self.communicator.read_serial_data()
        self.execute_command('throttle', pump=2,value=1)
        self.execute_command('off')
    
    def execute_command(self, command, **kwargs):
        if command in self.commands:
            self.commands[command](**kwargs)
        else:
            message = self.messages.create_json_message(
                self.name,"ALERT", "not ok", "Command was not understood")
            print(message)


