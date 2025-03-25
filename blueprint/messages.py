#type: ignore
"""
A message storage system for dict/json formatted information.

Author(s): BoB LeSuer
"""
import json
import sys
import os


# Needed to make testing a bit eaiser, but in production may not be necessary 
# Doesn't work on microcontroller. 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from blueprint.utility import check_if_microcontroller
if check_if_microcontroller():
    import adafruit_logging as logging
else:
    import logging

# Add custom levels to logging - allows us to eliminate the comm_type variable and possibly status

HEARTBEAT_LEVEL = 15    # Custom level for providing heartbeat-style unsolicited information
INSTRUCTION_LEVEL = 23  # Custom level for sending instructions
SUCCESS_LEVEL = 27      # Custom level for responding to an instruction successfully
PROBLEM_LEVEL = 35      # Custom level for responding to an instruction unsuccessfully

logging.addLevelName(HEARTBEAT_LEVEL, "HEARTBEAT")
logging.addLevelName(INSTRUCTION_LEVEL, "INSTRUCTION")
logging.addLevelName(PROBLEM_LEVEL, "PROBLEM")
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def heartbeat(self, message, *args, **kwargs):
    if self.isEnabledFor(HEARTBEAT_LEVEL):
        self._log(HEARTBEAT_LEVEL, message, args, **kwargs)

def instruction(self, message, *args, **kwargs):
    if self.isEnabledFor(INSTRUCTION_LEVEL):
        self._log(INSTRUCTION_LEVEL, message, args, **kwargs)

def problem(self, message, *args, **kwargs):
    if self.isEnabledFor(PROBLEM_LEVEL):
        self._log(PROBLEM_LEVEL, message, args, **kwargs)

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


logging.Logger.heartbeat = heartbeat
logging.Logger.instruction = instruction
logging.Logger.problem = problem
logging.Logger.success = success


def make_message(
        subsystem_name: str = None, 
        status: str = "Not Implemented", 
        meta: dict = None,
        payload: str = "", 
        jsonq: bool = False):
    """
    Creates a message with the given information in either json or dict format.
    """



    # Create the dictionary with the provided information
    message = {
        "subsystem_name": subsystem_name,
        "status": status,
        "meta": meta if meta else {},
        "payload": payload
    }

    # Return the desired format
    return json.dumps(message) if jsonq else message

def parse_payload(payload):
    """
    Parses a payload string and extracts relevant information.
    """
    if not isinstance(payload, str):
        # Might want to return nothing and log error instead, so program continues
        raise TypeError(f"Payload must be a string, not {type(payload)}")
    
    try:
        return json.loads(paylod)
    except json.JSONDecodeError:
        # Have not established an appropriate messaging stream.
        logging.warning('Payload is not valid JSON, attempting string parsing')

        # Now try to parse string
        parts  = payload.split()
        if not parts:
            return {} # Empty payload
        return {"func": parts[0], "args": parts[1:]}
    except Exception as e:
        logging.error(f"An unexpected error occured: {e}")
        raise # This forces that error to be re-raised


class MessageBuffer():
    """
    A class to manage a buffer of messages.
    """

    def __init__(self):
        """
        Initializes an empty message buffer.
        """
        self.messages = []
        self.max_messages = 100

    def is_empty(self):
        """
        Checks if the message buffer is empty.
        """
        return not self.messages
        # if above causes problems return len(self.messages) == 0

    def store_message(self, content: dict):
        """
        Stores a message in the buffer.
        """
        if not isinstance(content, dict):
            raise ValueError(f"Content should be dict but is {type(content)}")
        self.messages.append(content)

    def store_json(self, json_message: str):
        """
        Stores a JSON-formatted message in the buffer.
        """        
        try: 
            content = self.json_to_dict(json_message)
            if content is None:
                logging.error(f"Failed to parse JSON message: {json_message}")
                return
            self.store_message(content)
        except Exception as e:
            logging.error(f"Error storing JSON message: {e}")
            raise

    def get_oldest_message(self, jsonq: bool = False):
        """
        Retrieves the oldest message from the buffer.
        """
        try:
            message = self.messages.pop(0)
        except IndexError:
            return None

        return json.dumps(message) if jsonq else message

    def json_to_dict(self, message_json: str):
        """
        Converts a JSON-formatted message to a dictionary.
        """        
        try:
            return json.loads(message_json)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON, returning raw message. Error: {e}")
            return {"raw":message_json}
        except Exception as e:
            logging.error(f"Unexpected error occured during JSON parsing: {e}")
            return {}

    def dict_to_json(self, message_dict: dict):
        """
        Converts a dictionary to a JSON-formatted message.
       """        
        # Does not validate that `message_dict` is a Dict and will work with a string.
        return json.dumps(message_dict)

    def get_size_of_buffer(self):
        """
        Returns the size of the message buffer.
        """        
        return len(self.messages)

    def flush(self):
        """
        Clears all messages from the buffer.
        """
        self.messages = []
    
    def prune(self):
        """
        Removes oldest messages from a full buffer
        """
        if len(self.messages) > self.max_messages:
            to_remove = len(self.messages) - self.max_messages
            logging.warning(f"removing {to_remove} messages")
            self.messages = self.messages[to_remove:]

    @staticmethod
    def create_with_logging(subsystem_name='none', level=logging.INFO, logger_name='default'):
        """
        Creates a MessageBuffer and attaches a MessageBufferHandler to it.

        Args:
            subsystem_name: The subsystem name for the MessageBufferHandler.
            level: The logging level to set for the handler.
            logger_name: The name of the logger to use.

        Returns:
            A tuple containing the MessageBuffer and the logger.
        """
        message_buffer = MessageBuffer()
        log = logging.getLogger(logger_name)
        log.setLevel(level)
        message_handler = MessageBufferHandler(message_buffer, subsystem_name)
        log.addHandler(message_handler)
        return message_buffer, log

# Develop various methods for handling messages via logging. Presently using the custom serial buffer
class MessageBufferHandler(logging.Handler):
    """Custom logging handler."""

    def __init__(self, message_buffer, subsystem_name, datefmt=None):
        super().__init__()
        self.message_buffer = message_buffer
        self.subsystem_name = subsystem_name
        self.status = 'NA'
        self.print = False  # To override logging and simply print the message
        self.datefmt = datefmt # Keeping a separate variable that might be changed later
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt=self.datefmt)  # Instantiate the formatter


    def emit(self, record):
        """Emits a log record to the message buffer."""

        # Extract information from the LogRecord
        metadata = {
            "asctime": self.formatter.formatTime(record,self.datefmt),
            "name": record.name,
            "levelname": record.levelname,
        }
        print(record.msg)
        try:
            print(metadata['asctime'])
        except:
            print(dir(record))
        print(record.levelname)
        

        message = make_message(
            subsystem_name=self.subsystem_name,
            status=self.status,
            meta=metadata,
            payload=record.msg,
            jsonq=False
        )
        if self.print:
            print(message)
        else:
            self.message_buffer.store_message(message)


if __name__ == '__main__':
    # Create a message buffer
    message_buffer = MessageBuffer()

    # Create a logger
    log = logging.getLogger('example')
    log.setLevel(logging.INFO)

    # Create a custom handler and add it to the logger
    message_handler = MessageBufferHandler(message_buffer, subsystem_name='None')
    log.addHandler(message_handler)

    message_handler.setLevel(logging.WARNING)
    log.debug('this message should not be stored')
    log.critical('this message will be stored')
    message_handler.status='FAILED'
    log.warning('this message will also be stored')

    while not message_buffer.is_empty():
        print(message_buffer.get_oldest_message())

    mb, newlog = MessageBuffer.create_with_logging(subsystem_name='newone')
    newlog.warning('this message will be stored')

    while not mb.is_empty():
        print(mb.get_oldest_message())
