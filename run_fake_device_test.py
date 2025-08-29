import time
import json
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message

# This utility requires the adafruit-board-toolkit, which should be in requirements.txt
try:
    from adafruit_board_toolkit.circuitpython_serial import data_comports
except ImportError:
    print("Error: 'adafruit-board-toolkit' is not installed.")
    print("Please run 'pip install adafruit-board-toolkit'")
    exit()

def find_device_port():
    """Scans for and returns the first available CircuitPython data port."""
    ports = data_comports()
    if not ports:
        return None
    return ports[0].device

def main():
    """Main function to run the live test against the fake SDL device."""
    print("--- SDL Host Live Test ---")
    
    # 1. Find the connected CircuitPython device
    device_port = find_device_port()
    if not device_port:
        print("\nERROR: No CircuitPython device found. Make sure it is connected.")
        return

    print(f"\nFound device at: {device_port}")

    # 2. Set up the communication channel (Postman)
    # The timeout=0.1 makes the receive() call non-blocking
    postman_params = {"port": device_port, "baudrate": 115200, "timeout": 0.1, "protocol": "serial"}
    postman = SerialPostman(postman_params)
    
    try:
        postman.open_channel()
        print("Serial port opened successfully. Listening for messages...")
        print("Press Ctrl+C to exit.")

        last_blink_time = 0
        blink_interval = 10  # Send a blink command every 10 seconds

        # 3. Enter the main communication loop
        while True:
            # --- Check for incoming messages from the device ---
            raw_message_from_device = postman.receive()
            if raw_message_from_device:
                try:
                    # Attempt to parse the JSON string into a Message object
                    message = Message.from_json(raw_message_from_device)
                    print(f"\nRECEIVED <-- [{message.status}] {message.to_dict()}")
                except (json.JSONDecodeError, ValueError):
                    # If parsing fails, just print the raw data
                    print(f"\nRECEIVED RAW <-- {raw_message_from_device}")

            # --- Send a command periodically ---
            if time.time() - last_blink_time > blink_interval:
                print("\nSending blink command...")
                
                # Create the blink instruction message
                blink_payload = {"func": "blink", "args": ["3"]}
                blink_message = Message.create_message(
                    subsystem_name="HOST",
                    status="INSTRUCTION",
                    payload=blink_payload
                )

                # Send the serialized message to the device
                postman.send(blink_message.serialize())
                print(f"SENT --> [INSTRUCTION] {blink_message.to_dict()}")
                
                last_blink_time = time.time()

            # A short sleep to prevent the loop from using 100% CPU
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nExiting program.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # Ensure the serial port is closed on exit
        if postman.is_open:
            postman.close_channel()
            print("Serial port closed.")

if __name__ == "__main__":
    main()