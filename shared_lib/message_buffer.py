#type: ignore

# Base (abstract-ish) class for a buffer that will handle messages.
class MessageBuffer():
    """
    Base class for message buffer implementations.
    """

    def __init__(self, max_size: int = 100):
        """
        Initializes the message buffer.
        """
        self.messages = self._create_storage()  # Abstract method to create storage
        self.max_size = max_size  # Maximum capacity of the buffer (fixed)
        self.current_size = 0  # Track how many messages are in the buffer.  Important for Circular Buffer
        #This is for the circular buffer, but it won't hurt the others.
        self.head = 0
        self.tail = 0

    def is_empty(self) -> bool:
        """
        Returns True if the buffer is empty, False otherwise.
        """
        return self.current_size == 0

    def is_full(self) -> bool:
        """
        Returns True if the buffer is full, False otherwise.
        """
        return self.current_size >= self.max_size

    def store(self, value):
        """
        Stores a value in the message buffer.
        """
        if self.is_full():
            self._handle_full_buffer(value) # handle the exception if the buffer is full
            return
        self._store(value) #Implementation specific storing
        self.current_size += 1

    def get(self):
        """
        Retrieves the next message from the buffer (implementation-specific).
        """
        if self.is_empty():
            return None  # Or raise an exception if appropriate

        value = self._get() #Implementation specific retreival
        self.current_size -= 1
        return value

    def flush(self):
        """
        Empties the buffer.
        """
        self._flush() #Implementation specific flushing
        self.current_size = 0
        self.head = 0
        self.tail = 0

    def _create_storage(self):
      """Creates a new storage object"""
      return [] # implementation specific

    def _handle_full_buffer(self, value):
        """handles when the message buffer is full"""
        raise OverflowError("Buffer is full")

    def _store(self, value):
        """Stores a value in the buffer, Implementation Specific"""
        raise NotImplementedError("Implementation specific storing not implemented")

    def _get(self):
        """Retrieves a value from the buffer, Implementation Specific"""
        raise NotImplementedError("Implementation specific retrieval not implemented")

    def _flush(self):
        """flushes, implementation specific"""
        raise NotImplementedError("Implementation specific flush not implemented")

class LinearMessageBuffer(MessageBuffer):
    """
    A simple linear FIFO message buffer implemented using a list.
    """

    def __init__(self, max_size: int = 100):
        super().__init__(max_size)
    
    def _create_storage(self):
        return []

    def _store(self, value):
        self.messages.append(value)

    def _get(self):
        return self.messages.pop(0)

    def _flush(self):
        self.messages = []


class CircularMessageBuffer(MessageBuffer):
    """
    A circular FIFO message buffer implemented using a list.
    """

    def __init__(self, max_size: int = 100):
        super().__init__(max_size)
        
    def _create_storage(self):
        return [None] * self.max_size #initialize with None

    def _handle_full_buffer(self, value):
        self._get() #this handles the exception that happens on this circular buffer

    def _store(self, value):
        self.messages[self.tail] = value
        self.tail = (self.tail + 1) % self.max_size

        if self.is_full():
            self.head = (self.head + 1) % self.max_size # If full, also advance the head

    def _get(self):
        if self.is_empty():
            return None  # Or raise an exception if appropriate

        value = self.messages[self.head]
        self.messages[self.head] = None # clean the previous data
        self.head = (self.head + 1) % self.max_size
        return value

    def _flush(self):
        self.messages = [None] * self.max_size
        self.head = 0
        self.tail = 0