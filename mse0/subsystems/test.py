# type: ignore
from mse0.sdl_communicator import sdlCommunicator
from mse0.messages import make_message
import time

class sdlTest:
    '''
    A test subsytem for - you know - testing
    '''

    # Functions registered in the commands dictionary must be defined before __init__
    
    def my_func_1(self, **kwargs):
        """
        Sample function that has keywords.
        """
        values_passed = "Received: "
        for key, value in kwargs.items():
            values_passed = values_passed + f'{key}({value})'
        
        message = make_message(
            self.name,"RESPONSE", "SUCCESS", 
            values_passed)
        print(message)

    def my_func_2(self):
        """ 
        Sample function
        """
        message = make_message(
            self.name,"RESPONSE", "SUCCESS", 
            f"Operation received")
        print(message)
        
    def __init__(self):
        self.name = "Test"
        self.version = "0.1"
        self.description = "Subsystem testing functionality and serving as a template"
        self.communicator = sdlCommunicator(self.name)
        self.commands = {
            "f1": self.my_func_1,
            "f2": self.my_func_2,
        }


        
    def run(self, loglevel = 1):
        """
        poll for commands
        check for errors
        send information based upon log level
        """
        self.loglevel = loglevel # Reserved for future use
        while True:
            self.communicator.read_serial_data()
            if not self.communicator.readbuffer.is_empty():
                print(self.communicator.readbuffer.get_oldest_message())
            time.sleep(1)
            
        #self.execute_command('f1', pump=2,value="hi there")
        #self.execute_command('f2')
    
    def execute_command(self, command, **kwargs):
        if command in self.commands:
            self.commands[command](**kwargs)
        else:
            message = make_message(
                self.name,"ALERT", "not ok", "Command was not understood")
            print(message)
