import unittest
import json
from blueprint.messages import parse_payload


class TestParsePayload(unittest.TestCase):
    def test_valid_json_payload(self):
        payload = '{"func": "test_func", "arg1": "value1", "arg2": "value2"}'
        expected_output = {"func": "test_func", "arg1": "value1", "arg2": "value2"}
        self.assertEqual(parse_payload(payload), expected_output)

    def test_regular_string_payload(self):
        payload = "test_func arg1 arg2"
        expected_output = {"func": "test_func", "arg1": "arg1", "arg2": "arg2"}
        self.assertEqual(parse_payload(payload), expected_output)

    def test_string_with_keyword_arguments(self):
        payload = "test_func arg1=val1 arg2=val2"
        expected_output = {"func": "test_func", "arg1": "val1", "arg2": "val2"}
        self.assertEqual(parse_payload(payload), expected_output)

    def test_non_string_payload(self):
        payload = 12345
        with self.assertRaises(TypeError):
            parse_payload(payload)

if __name__ == '__main__':
    unittest.main()
