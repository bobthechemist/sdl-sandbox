# shared_lib/command_library.py
#type: ignore

from .messages import Message

# 1. This decorator is simple and works perfectly in CircuitPython.
def command(name: str):
    """A decorator to register a method as a command handler."""
    def wrapper(func):
        # Attach metadata to the function object itself
        func._command_name = name
        return func
    return wrapper

class CommonCommandHandler:
    """
    A helper class that provides handlers for standard, common commands
    that all devices should support.
    """
    def __init__(self, machine, supported_commands: dict):
        """
        Initializes the handler.

        Args:
            machine: The StateMachine instance this handler will act upon.
            supported_commands: The device's specific command dictionary.
        """
        self.machine = machine
        self.supported_commands = supported_commands

    @classmethod
    def generate_command_dict(cls) -> dict:
        """
        Generates a dictionary of common commands by inspecting class methods.
        
        This method is CircuitPython-safe and does not use the 'inspect' module.
        It scans for methods decorated with @command and extracts information
        from their __doc__ attribute.
        """
        common_commands = {}
        # 2. Use dir() to get all attribute names of the class.
        for attr_name in dir(cls):
            # Get the attribute object (e.g., a function) from its name.
            method = getattr(cls, attr_name)
            
            # Check if it's a function with our special '_command_name' attribute.
            if callable(method) and hasattr(method, '_command_name'):
                command_name = method._command_name
                description, args = cls._parse_docstring(method)
                common_commands[command_name] = {
                    "description": description,
                    "args": args
                }
        return common_commands

    @staticmethod
    def _parse_docstring(func) -> tuple[str, list]:
        """
        Parses the __doc__ attribute of a function to get a description.
        
        This is a lightweight, CircuitPython-safe alternative to inspect.getdoc().
        """
        # 3. Access the __doc__ attribute directly.
        docstring = getattr(func, '__doc__', None)
        if not docstring:
            return "No description available.", []

        # Simple parsing: clean up whitespace and take the first line.
        lines = docstring.strip().split('\n')
        description = lines[0].strip()
        
        # This is where you would add logic to parse arguments if needed.
        args = []
        
        return description, args

    def get_handlers(self) -> dict:
        """
        Returns a dictionary of common command handlers that can be merged
        into a state's command dispatcher. (CircuitPython-safe version)
        """
        handlers = {}
        # Iterate over attributes of the INSTANCE to get the bound methods.
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            # Check if it's a callable method with our decorator's attribute.
            if callable(method) and hasattr(method, '_command_name'):
                handlers[method._command_name] = method
        return handlers

    # Decorators are applied to the handler methods exactly as before.
    @command("help")
    def _handle_help(self, payload):
        """Returns a list of all supported commands and their arguments."""
        # The docstring's first line is the description.
        # The payload is ignored for this command.
        self.machine.log.info("Help command received. Sending capabilities.")
        response = Message.create_message(
            subsystem_name=self.machine.name,
            status="SUCCESS",
            payload=self.supported_commands
        )
        self.machine.postman.send(response.serialize())

    @command("ping")
    def _handle_ping(self, payload):
        """Sends a SUCCESS response to verify the device is alive."""
        # This is used to verify the device is alive and responsive.
        # The payload is ignored for this command.
        self.machine.log.info("Ping received. Responding.")
        response = Message.create_message(
            subsystem_name=self.machine.name,
            status="SUCCESS",
            payload={"response": "pong"}
        )
        self.machine.postman.send(response.serialize())