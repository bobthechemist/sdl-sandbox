# type: ignore
#from adafruit_motorkit import MotorKit #commented out for debugging purposes
import time

class sdlPumps:
    """
    Controls a series of four peristaltic pumps.
    """

    valid_commands = []

    def __init__(self, pwm_frequency=1600):
        """
        Initializes the pump subsystem
        """
        #self.kit = MotorKit() #commented out for debugging purposes

    def throttle(self, motor, value):
        """
        Sets the speed of a pump (1 .. 4) from max forward (1) to max backwards (-1)
        """
        if 1 <= value <= 4:
            # do something
        else:
            # do something else
            

