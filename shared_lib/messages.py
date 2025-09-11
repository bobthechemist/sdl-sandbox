#type: ignore
import json


class Message():
    """
    Represents a message with subsystem name, status, metadata, and payload.
    """

    VALID_STATUS = {"DEBUG", "TELEMETRY", "INFO", "INSTRUCTION", "SUCCESS", "PROBLEM", "WARNING", "DATA_RESPONSE"}

    def __init__(self, subsystem_name=None, status=None, meta=None, payload=None):
        """Initializes a Message object."""
        self._subsystem_name = subsystem_name
        # Validate that the status provided to the method is valid
        if status is not None and status not in Message.VALID_STATUS:
           raise ValueError("Invalid Status Level")
        self._status = status
        if meta is None:
            self._meta = {}
        elif not isinstance(meta, dict):
            raise TypeError("meta must be a dictionary")
        else:
            self._meta = meta
        self._payload = payload

    def to_dict(self):
        """Returns a dictionary representation of the message."""
        return {
            "subsystem_name": self.subsystem_name,
            "status": self.status,
            "meta": self.meta,
            "payload": self.payload
        }

    def serialize(self):
        """Serializes the message to JSON."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_string: str):
        """
        Creates a new Message instance from a JSON string.
        This is a class method.
        """
        try:
            data = json.loads(json_string)
            subsystem_name = data.get("subsystem_name")
            status = data.get("status")
            meta = data.get("meta", {})
            payload = data.get("payload")

            # The validation for status is handled by the __init__ method,
            # so we just pass the values along.
            return cls(
                subsystem_name=subsystem_name,
                status=status,
                meta=meta,
                payload=payload
            )
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")

    @property
    def subsystem_name(self):
        return self._subsystem_name

    @subsystem_name.setter
    def subsystem_name(self, value):
        self._subsystem_name = value

    @property
    def status(self):
        return self._status

    # Remove the setter
    # @status.setter
    # def status(self, value):
    #     #Validate that we can set it if its a valid status
    #     if value is not None and value not in Message.VALID_STATUS:
    #         raise ValueError("Invalid Status Level")
    #     self._status = value

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, value):
        if not isinstance(value, dict):
            raise TypeError("meta must be a dictionary")
        self._meta = value

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    @classmethod
    def create_message(cls, subsystem_name=None, status=None, meta=None, payload=None):
        """Creates a Message instance."""
        return cls(subsystem_name=subsystem_name, status=status, meta=meta, payload=payload)

    @classmethod
    def get_valid_status(cls):
        return cls.VALID_STATUS

