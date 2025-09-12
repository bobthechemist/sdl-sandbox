import time
import json
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message

# Import utilities from the host application part of the stack
from communicate.host_utilities import find_data_comports
from host_app.firmware_db import FIRMWARE_DATABASE

def send_command_and_wait_for_response(postman: SerialPostman, device_name: str, command_payload: dict, timeout: int = 25):
    """
    Sends a command to a device and waits for a SUCCESS or PROBLEM response.
    Ignores other message types like TELEMETRY.
    
    Args:
        postman: The active SerialPostman instance for the device.
        device_name: The name of the device for logging purposes.
        command_payload: The dictionary for the message payload (e.g., {"func": "home", "args": {}}).
        timeout: How many seconds to wait for a response.
        
    Returns:
        The parsed Message object on success, or None on failure/timeout.
    """
    message = Message.create_message(
        subsystem_name="HOST_SCRIPT",
        status="INSTRUCTION",
        payload=command_payload
    )
    
    # Send the command
    postman.send(message.serialize())
    print(f"[{device_name}] SENT --> {message.to_dict()}")

    # Wait for a relevant response
    start_time = time.time()
    while time.time() - start_time < timeout:
        raw_response = postman.receive()
        if raw_response:
            try:
                response_msg = Message.from_json(raw_response)
                # We only care about SUCCESS or PROBLEM as a direct reply
                if response_msg.status in ("SUCCESS", "PROBLEM"):
                    print(f"[{device_name}] RECV <-- {response_msg.to_dict()}")
                    return response_msg
                else:
                    # Log other messages but continue waiting
                    print(f"[{device_name}] (Ignoring) RECV <-- {response_msg.to_dict()}")
            except (json.JSONDecodeError, ValueError):
                print(f"[{device_name}] RECV RAW <-- {raw_response}")
        time.sleep(0.1)
    
    print(f"[{device_name}] ERROR: Did not receive a response for '{command_payload['func']}' within {timeout}s.")
    return None

def main():
    """
    Main script to run the measurement workflow.
    """
    print("====== Measurement Workflow Script Started ======")

    # 1. Discover and identify devices
    print("\n[Step 1] Scanning for devices...")
    all_ports = find_data_comports()
    if not all_ports:
        print("ERROR: No devices found.")
        return

    identified_devices = {}
    for port_info in all_ports:
        vid, pid = port_info['VID'], port_info['PID']
        manufacturer_info = FIRMWARE_DATABASE.get(vid, {})
        product_name = manufacturer_info.get('products', {}).get(pid, "Unknown")
        print(f"  - Found '{product_name}' on port {port_info['port']}")
        if "sidekick" in product_name.lower():
            identified_devices['sidekick'] = port_info
        elif "colorimeter" in product_name.lower():
            identified_devices['colorimeter'] = port_info
    
    if 'sidekick' not in identified_devices or 'colorimeter' not in identified_devices:
        print("\nERROR: Could not find both a Sidekick and a Colorimeter. Aborting workflow.")
        return

    # 2. Establish connections
    sidekick_port = identified_devices['sidekick']['port']
    colorimeter_port = identified_devices['colorimeter']['port']
    sidekick_postman = None
    colorimeter_postman = None
    
    try:
        print("\n[Step 2] Establishing connections...")
        sk_params = {"port": sidekick_port, "baudrate": 115200, "timeout": 0.1, "protocol": "serial"}
        sidekick_postman = SerialPostman(sk_params)
        sidekick_postman.open_channel()
        
        cm_params = {"port": colorimeter_port, "baudrate": 115200, "timeout": 0.1, "protocol": "serial"}
        colorimeter_postman = SerialPostman(cm_params)
        colorimeter_postman.open_channel()
        
        # Give devices a moment to initialize after connection
        time.sleep(2)
        sidekick_postman.channel.reset_input_buffer()
        colorimeter_postman.channel.reset_input_buffer()
        print("  - Connections established with both devices.")

        # 3. Setup phase: Set time on both devices
        print("\n[Step 3] Setting device clocks...")
        time_payload = {"func": "set_time", "args": {"epoch_seconds": int(time.time())}}
        send_command_and_wait_for_response(sidekick_postman, "Sidekick", time_payload)
        send_command_and_wait_for_response(colorimeter_postman, "Colorimeter", time_payload)

        # 4. Home the Sidekick
        print("\n[Step 4] Homing the Sidekick arm. This may take a moment...")
        home_payload = {"func": "home", "args": {}}
        response = send_command_and_wait_for_response(sidekick_postman, "Sidekick", home_payload)
        if not response or response.status != 'SUCCESS':
            print("ERROR: Sidekick failed to home. Aborting workflow.")
            return
        print("  - Sidekick homing complete.")

        # 5. Move the Sidekick to the measurement position
        print("\n[Step 5] Moving Sidekick to measurement position (10, -2)...")
        move_payload = {"func": "move_to", "args": {"x": 10.0, "y": -2.0}}
        response = send_command_and_wait_for_response(sidekick_postman, "Sidekick", move_payload)
        if not response or response.status != 'SUCCESS':
            print("ERROR: Sidekick failed to move. Aborting workflow.")
            return
        print("  - Sidekick is in position.")

        # 6. Trigger the Colorimeter measurement
        print("\n[Step 6] Taking a colorimeter measurement...")
        read_payload = {"func": "read_all", "args": {}}
        response = send_command_and_wait_for_response(colorimeter_postman, "Colorimeter", read_payload)
        
        if response and response.status == 'SUCCESS':
            print("\n--- MEASUREMENT RESULT ---")
            # The payload itself is the dictionary of readings
            measurement_data = response.payload
            print(json.dumps(measurement_data, indent=2))
            print("--------------------------")
        else:
            print("ERROR: Failed to get a reading from the colorimeter.")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the workflow: {e}")
    finally:
        # 7. Cleanup: Ensure all connections are closed
        print("\n[Step 7] Closing connections...")
        if sidekick_postman and sidekick_postman.is_open:
            sidekick_postman.close_channel()
            print("  - Sidekick connection closed.")
        if colorimeter_postman and colorimeter_postman.is_open:
            colorimeter_postman.close_channel()
            print("  - Colorimeter connection closed.")
        
    print("\n====== Measurement Workflow Script Finished ======")

if __name__ == "__main__":
    main()