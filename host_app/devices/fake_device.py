# host_app/devices/fake_device.py
import logging
from shared_lib.message_buffer import LinearMessageBuffer
from communicate.postman import DummyPostman
from communicate.secretary import SecretaryStateMachine, Router, CircularFiler
from shared_lib.statemachine import State, StateMachine
from shared_lib.messages import Message
import json

# Set up logging for the fake device
# NOTE: Using a basicConfig here can sometimes interfere with other logging configurations.
# For a larger application, it's often better to configure logging at the entry point (main.py).
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger("FakeDevice")

class FakeInstrumentSubsystemRouter(Router):
    """
    A simple router for the FakeDevice. In a real device, this would
    direct messages to specific hardware control state machines.
    For the fake device, we'll just log and maybe simulate a response.
    """
    def __init__(self, device_name: str, outbox: LinearMessageBuffer):
        self.device_name = device_name
        self.outbox = outbox
        log.info(f"Router for {device_name} initialized.")

    def route(self, message: Message):
        log.info(f"FakeInstrumentRouter received message for '{self.device_name}': {message.to_dict()}")
        # Simulate a response to an "INSTRUCTION"
        if message.status == "INSTRUCTION":
            payload_data = message.payload # Assuming payload is already a dict
            log.info(f"FakeInstrumentRouter: Processing instruction payload: {payload_data}")

            # Example: Simulate turning on/off an LED
            if isinstance(payload_data, dict) and payload_data.get("func") == "set_led":
                led_state = payload_data.get("args", ["off"])[0] # Get first arg, default 'off'
                response_payload = {"status": "LED set to " + str(led_state)}
                response_status = "SUCCESS"
                log.info(f"FakeInstrument: LED is now {led_state}")
            else:
                response_payload = {"error": "Unknown instruction or malformed payload."}
                response_status = "PROBLEM"

            # Create a response message
            response_message = Message.create_message(
                subsystem_name=self.device_name,
                status=response_status,
                payload=response_payload
            )
            self.outbox.store(response_message)
            log.info(f"FakeInstrumentRouter: Stored response in outbox: {response_message.to_dict()}")
        # else: Just acknowledge other messages (HEARTBEAT, INFO) without response

class FakeDevice:
    """
    A software-only representation of a scientific instrument.
    It uses a DummyPostman to simulate serial communication.
    """
    def __init__(self, name="FakeInstrument"):
        self.name = name
        self.postman = DummyPostman(params={"protocol": "dummy"})
        self.postman.open_channel()
        self.inbox = LinearMessageBuffer()
        self.outbox = LinearMessageBuffer()
        self.subsystem_router = FakeInstrumentSubsystemRouter(name, self.outbox)
        # Using a base Filer that does nothing, as CircularFiler prints. For tests, silence is better.
        self.filer = CircularFiler({'print': False})
        self.secretary = SecretaryStateMachine(
            inbox=self.inbox,
            outbox=self.outbox,
            subsystem_router=self.subsystem_router,
            filer=self.filer,
            postman=self.postman,
            name=f"{self.name}_Secretary"
        )
        self.secretary.run() # Start the secretary's state machine

        log.info(f"FakeDevice '{self.name}' initialized with DummyPostman.")

    def send_command(self, payload_dict: dict):
        """
        Simulates sending a command *to* the fake device.
        This will be received by its internal DummyPostman.
        """
        cmd_message = Message.create_message(
            subsystem_name="HOST", # Message is from the host
            status="INSTRUCTION",
            payload=payload_dict
        )
        # Store message in the DummyPostman's canned_responses buffer
        # This simulates the host sending a message that the device's Postman will receive
        self.postman.canned_responses.append(cmd_message.serialize())
        log.info(f"Host: Sent command to FakeDevice: {cmd_message.to_dict()}")


    def read_responses(self):
        """
        Reads any messages the fake device has sent back via its DummyPostman.
        DEPRECATED in favor of get_sent_by_fake_device which is more explicit.
        """
        return self.get_sent_by_fake_device()

    def update(self):
        """
        Simulates the device's main loop.
        1. Check for incoming data from the postman (as a raw string).
        2. If data exists, parse it into a Message object.
        3. Place the Message object in the secretary's inbox.
        4. Update the secretary state machine, which will now process it.
        """
        # Step 1: Check for incoming messages from the "outside world"
        raw_incoming_message = self.postman.receive() # Pulls from canned_responses
        if raw_incoming_message:
            log.info(f"FakeDevice: Received raw message from Postman: {raw_incoming_message}")
            try:
                # Step 2 & 3: Parse the message and store it in the secretary's inbox
                message = Message.from_json(raw_incoming_message)
                self.secretary.inbox.store(message) # Store the PARSED message object
            except (ValueError, json.JSONDecodeError) as e:
                log.error(f"Failed to parse incoming message: {raw_incoming_message}. Error: {e}")

        # Step 4: Now, update the secretary. If a message was stored, it will process it.
        self.secretary.update()

    def get_sent_by_fake_device(self):
        """
        Retrieve messages the fake device has "sent" out (which means they are
        in the DummyPostman's sent_values list).
        """
        sent_messages = []
        # get_sent_values() returns a list of raw JSON strings
        for raw_msg_str in self.postman.get_sent_values():
            try:
                # We need to parse the JSON string back into a Message object
                msg = Message.from_json(raw_msg_str)
                sent_messages.append(msg)
            except (ValueError, json.JSONDecodeError) as e:
                log.error(f"Failed to parse sent message: {raw_msg_str}. Error: {e}")
        self.postman.clear_sent_values() # Clear after reading
        return sent_messages

    def stop(self):
        self.secretary.stop()
        log.info(f"FakeDevice '{self.name}' stopped.")