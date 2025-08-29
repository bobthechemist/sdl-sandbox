# tests/host_app/test_fake_device.py
import unittest
from host_app.devices.fake_device import FakeDevice
from shared_lib.messages import Message
import json

class TestFakeDevice(unittest.TestCase):

    def setUp(self):
        self.fake_device = FakeDevice("TestFakeDevice")

    def tearDown(self):
        self.fake_device.stop()

    def test_initialization(self):
        self.assertIsNotNone(self.fake_device.secretary)
        self.assertTrue(self.fake_device.secretary.running)
        self.assertEqual(self.fake_device.secretary.name, "TestFakeDevice_Secretary")

    def test_send_and_receive_instruction(self):
        # 1. Host sends an instruction to the fake device
        instruction_payload = {"func": "set_led", "args": ["on"]}
        self.fake_device.send_command(instruction_payload)

        # 2. FIX: Allow the fake device's secretary to process the incoming message over several cycles.
        #    A single update is not enough for Monitoring -> Reading -> Routing -> Filing -> Monitoring -> Sending.
        for _ in range(5):
            self.fake_device.update()

        # 3. Check what the fake device "sent back" (stored in its DummyPostman's sent_values)
        responses = self.fake_device.get_sent_by_fake_device()

        self.assertEqual(len(responses), 1, "Should have received exactly one response.")
        response_message = responses[0]

        self.assertEqual(response_message.subsystem_name, "TestFakeDevice")
        self.assertEqual(response_message.status, "SUCCESS")
        # Payload is a dict, so we need to compare dicts
        self.assertEqual(response_message.payload, {"status": "LED set to on"})

    def test_unknown_instruction(self):
        instruction_payload = {"func": "do_something_unknown"}
        self.fake_device.send_command(instruction_payload)

        # FIX: Also requires multiple updates
        for _ in range(5):
            self.fake_device.update()

        responses = self.fake_device.get_sent_by_fake_device()
        self.assertEqual(len(responses), 1)
        response_message = responses[0]

        self.assertEqual(response_message.subsystem_name, "TestFakeDevice")
        self.assertEqual(response_message.status, "PROBLEM")
        self.assertIn("error", response_message.payload)


    def test_multiple_messages(self):
        # Send a few commands
        self.fake_device.send_command({"func": "set_led", "args": ["on"]})
        self.fake_device.send_command({"func": "set_led", "args": ["off"]})

        # Process multiple times. Need more updates for more messages.
        for _ in range(10):
            self.fake_device.update()

        responses = self.fake_device.get_sent_by_fake_device()
        self.assertEqual(len(responses), 2)

        self.assertEqual(responses[0].payload, {"status": "LED set to on"})
        self.assertEqual(responses[1].payload, {"status": "LED set to off"})

if __name__ == '__main__':
    unittest.main()