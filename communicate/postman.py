#type: ignore

class Postman():
    """
    Base class for message transmission between devices.
    """

    def __init__(self, params: dict):
        """
        Initializes the Postman with a dictionary of parameters.

        Args:
            params: A dictionary containing the configuration parameters.
                   Required Keys: "protocol" (e.g., "serial", "rest", "mqtt")
                   Optional Keys (depending on protocol):
                       "port" (for serial)
                       "baudrate" (for serial, default 115200)
                       "timeout" (for serial, default 1)
                       "url" (for REST)
                       "topic" (for MQTT)
                       ... (other protocol-specific parameters)
        """
        self.params = params
        self.protocol = params.get("protocol")
        if not self.protocol:
            raise ValueError("Protocol must be specified in params")

        self.channel = None
        self.is_open = False

    def open_channel(self):
        """
        Opens the communication channel (implementation-specific).
        """
        if self.is_open:
            return  # Do nothing if already open.  Raise exception?

        self.channel = self._open_channel()
        self.is_open = True

    def close_channel(self):
        """
        Closes the communication channel (implementation-specific).
        """
        if not self.is_open:
            return  # Do nothing if already closed. Raise exception?

        self._close_channel()
        self.channel = None
        self.is_open = False

    def send(self, value):
        """
        Sends a message (implementation-specific).
        """
        if not self.is_open:
            raise ValueError("Channel is not open.  Must call open_channel() first.")
        self._send(value)

    def receive(self):
        """
        Receives a message (implementation-specific).
        """
        if not self.is_open:
            raise ValueError("Channel is not open.  Must call open_channel() first.")
        return self._receive()

    # Implementation specific

    def _open_channel(self):
        """implementation to open channel"""
        raise NotImplementedError("Implementation specific open not implemented")

    def _close_channel(self):
        """implementation to close channel"""
        raise NotImplementedError("Implementation specific close not implemented")

    def _send(self, value):
        """implementation to send"""
        raise NotImplementedError("Implementation specific send not implemented")

    def _receive(self):
        """implementation to receive"""
        raise NotImplementedError("Implementation specific receive not implemented")