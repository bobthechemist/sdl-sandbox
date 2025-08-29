import unittest
import time
import json

# Import necessary classes from your project
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message
from adafruit_board_toolkit.circuitpython_serial import data_comports

# --- Test Configuration ---
# Timeout for waiting for a response from the device, in seconds.
# The device sends a heartbeat every 5s, so this should be longer than that.
DEVICE_RESPONSE_TIMEOUT = 7 

def find_device_port():
    """Scans for and returns the first available CircuitPython data port."""
    ports = data_comports()
    return ports[0].device if ports else None

# Get the device port once when the module is loaded.
# This is a condition for running the tests in this class.
DEVICE_PORT = find_device_port()

@unittest.skipIf(DEVICE_PORT is None, "Hardware Test: No CircuitPython device found.")
class TestFakeFirmwareIntegration(unittest.TestCase):
    """
    An integration test case that communicates with a live microcontroller
    running the 'fake' firmware.
    
    This is NOT a pure unit test. It requires:
    1. A CircuitPython board to be physically connected via USB.
    2. The 'fake' firmware to be loaded and running on the board.
    """

    def setUp(self):
        """
        This method runs before each test. It finds the device and
        opens the serial connection.
        """
        self.assertIsNotNone(DEVICE_PORT, "setUp failed: Device port should not be None.")
        
        postman_params = {
            "port": DEVICE_PORT,
            "baudrate": 115200,
            "timeout": 0.1,  # Non-blocking timeout
            "protocol": "serial"
        }
        self.postman = SerialPostman(postman_params)
        self.postman.open_channel()
        
        # Give the connection a moment to establish
        time.sleep(1)
        
        # Flush any old data from the device's serial buffer
        # The channel is the underlying pyserial object
        self.postman.channel.reset_input_buffer()
        print(f"\nConnected to {DEVICE_PORT}...")

    def tearDown(self):
        """
        This method runs after each test. It ensures the serial
        connection is closed.
        """
        if self.postman and self.postman.is_open:
            self.postman.close_channel()
            print("Disconnected.")

    def _listen_for_message(self, target_status: str, timeout: float) -> Message | None:
        """Helper function to listen for a specific message type within a timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            raw_data = self.postman.receive()
            if raw_data:
                try:
                    message = Message.from_json(raw_data)
                    print(f"  - Received: [{message.status}]")
                    if message.status == target_status:
                        return message
                except (json.JSONDecodeError, ValueError):
                    print(f"  - Received unparseable data: {raw_data}")
            time.sleep(0.1) # Don't spam the CPU
        return None

    def test_01_receive_heartbeat(self):
        """
        Verify that the host can receive an unsolicited HEARTBEAT message.
        """
        print("--- Test: Receiving HEARTBEAT ---")
        print(f"Listening for up to {DEVICE_RESPONSE_TIMEOUT} seconds...")
        
        heartbeat_msg = self._listen_for_message("HEARTBEAT", DEVICE_RESPONSE_TIMEOUT)
        
        self.assertIsNotNone(heartbeat_msg, f"Did not receive a HEARTBEAT within {DEVICE_RESPONSE_TIMEOUT}s.")
        self.assertEqual(heartbeat_msg.subsystem_name, "FAKE")
        self.assertIn("analog_value", heartbeat_msg.payload)
        self.assertIsInstance(heartbeat_msg.payload["analog_value"], int)

    def test_02_send_blink_and_get_success(self):
        """
        Verify that the host can send an INSTRUCTION and receive a SUCCESS response.
        """
        print("--- Test: Send BLINK, receive SUCCESS ---")
        
        # 1. Arrange: Create the blink command
        blink_payload = {"func": "blink", "args": ["2"]} # Blink twice
        blink_message = Message.create_message(
            subsystem_name="HOST",
            status="INSTRUCTION",
            payload=blink_payload
        )

        # 2. Act: Send the command
        print(f"Sending INSTRUCTION: {blink_message.to_dict()}")
        self.postman.send(blink_message.serialize())
        
        # 3. Assert: Listen for the SUCCESS response
        print(f"Listening for SUCCESS response for up to {DEVICE_RESPONSE_TIMEOUT} seconds...")
        success_msg = self._listen_for_message("SUCCESS", DEVICE_RESPONSE_TIMEOUT)

        self.assertIsNotNone(success_msg, f"Did not receive a SUCCESS response within {DEVICE_RESPONSE_TIMEOUT}s.")
        self.assertEqual(success_msg.subsystem_name, "FAKE")
        self.assertIn("Completed 2 blinks", success_msg.payload.get("detail", ""))


if __name__ == '__main__':
    unittest.main()