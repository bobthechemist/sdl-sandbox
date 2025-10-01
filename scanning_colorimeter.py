import time
import json
import csv
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message
import numpy as np

# Import utilities from the host application part of the stack
from communicate.host_utilities import find_data_comports
from host_app.firmware_db import FIRMWARE_DATABASE

def send_command_and_wait(postman: SerialPostman, device_name: str, command_payload: dict, valid_statuses: tuple = ("SUCCESS", "PROBLEM"), timeout: int = 5):
    """
    Sends a command to a device and waits for a specific response status.
    """
    message = Message.create_message(
        subsystem_name="HOST_SCRIPT",
        status="INSTRUCTION",
        payload=command_payload
    )
    
    postman.send(message.serialize())
    print(f"[{device_name}] SENT --> {message.to_dict()}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        raw_response = postman.receive()
        if raw_response:
            try:
                response_msg = Message.from_json(raw_response)
                if response_msg.status in valid_statuses:
                    print(f"[{device_name}] RECV <-- {response_msg.to_dict()}")
                    return response_msg
                else:
                    print(f"[{device_name}] (Ignoring) RECV <-- {response_msg.to_dict()}")
            except (json.JSONDecodeError, ValueError):
                print(f"[{device_name}] RECV RAW <-- {raw_response}")
        time.sleep(0.1)
    
    print(f"[{device_name}] ERROR: No valid response for '{command_payload['func']}' within {timeout}s. Expected one of {valid_statuses}.")
    return None

def main():
    """
    Main script to run the measurement workflow.
    """
    print("====== Measurement Workflow Script Started ======")
    results_data = []
    sidekick_postman = None
    colorimeter_postman = None

    try:
        # 1. Discover and identify devices
        print("\n[Step 1] Scanning for devices...")
        all_ports = find_data_comports()
        identified_devices = {}
        for port_info in all_ports:
            vid, pid = port_info['VID'], port_info['PID']
            mfg_info = FIRMWARE_DATABASE.get(vid, {})
            p_name = mfg_info.get('products', {}).get(pid, "Unknown")
            print(f"  - Found '{p_name}' on port {port_info['port']}")
            if "sidekick" in p_name.lower():
                identified_devices['sidekick'] = port_info
            elif "colorimeter" in p_name.lower():
                identified_devices['colorimeter'] = port_info
        
        if 'sidekick' not in identified_devices or 'colorimeter' not in identified_devices:
            raise RuntimeError("Could not find both a Sidekick and a Colorimeter.")

        # 2. Establish connections
        print("\n[Step 2] Establishing connections...")
        sk_port = identified_devices['sidekick']['port']
        cm_port = identified_devices['colorimeter']['port']
        
        # <<< FIX: Added "protocol": "serial" key back to the parameters dictionary
        sk_params = {"port": sk_port, "baudrate": 115200, "timeout": 0.1, "protocol": "serial"}
        sidekick_postman = SerialPostman(sk_params)
        sidekick_postman.open_channel()
        
        # <<< FIX: Added "protocol": "serial" key back to the parameters dictionary
        cm_params = {"port": cm_port, "baudrate": 115200, "timeout": 0.1, "protocol": "serial"}
        colorimeter_postman = SerialPostman(cm_params)
        colorimeter_postman.open_channel()
        
        time.sleep(2)
        sidekick_postman.channel.reset_input_buffer()
        colorimeter_postman.channel.reset_input_buffer()
        print("  - Connections established.")

        # 3. Setup phase
        print("\n[Step 3] Setting device clocks and homing Sidekick...")
        time_payload = {"func": "set_time", "args": {"epoch_seconds": int(time.time())}}
        send_command_and_wait(sidekick_postman, "Sidekick", time_payload)
        send_command_and_wait(colorimeter_postman, "Colorimeter", time_payload)

        home_payload = {"func": "home", "args": {}}
        home_response = send_command_and_wait(sidekick_postman, "Sidekick", home_payload, timeout=60)
        if not home_response or home_response.status != 'SUCCESS':
            raise RuntimeError("Sidekick failed to home.")
        print("❤️  - should not be moving")
        # States need a "ready" command. Perhaps we need a only execute on IDLE?
        move_payload = {"func": "move_to", "args":{"x":9.5,"y":-4}}
        move_response = send_command_and_wait(sidekick_postman,"Sidekick",move_payload, timeout=60)
        if not move_response or move_response.status != 'SUCCESS':
            print(f"  - WARNING: Failed to move to y={y_pos}. Skipping measurement.")
            
        sys.exit()
        time.sleep(5)
        # 4. Prepare for Scan
        print("\n[Step 4] Turning on colorimeter LED...")
        led_on_payload = {"func": "set", "args": {"led": True}}
        led_on_response = send_command_and_wait(colorimeter_postman, "Colorimeter", led_on_payload)
        if not led_on_response or led_on_response.status != 'SUCCESS':
            raise RuntimeError("Failed to turn on colorimeter LED.")
        
        print("  - LED is on. Waiting 1 second for stabilization...")
        time.sleep(1)

        # 5. Execute Scanning Loop
        print("\n[Step 5] Starting Y-axis scan from -4 to 4.5...")
        x_pos = 9.5
        channel_names = ["violet", "indigo", "blue", "cyan", "green", "yellow", "orange", "red"]

        for y_pos in np.random.permutation(np.arange(-4, 4, 1)):
            print(f"\n--- Processing position (x={x_pos}, y={y_pos}) ---")
            
            move_payload = {"func": "move_to", "args": {"x": x_pos, "y": float(y_pos)}}
            move_response = send_command_and_wait(sidekick_postman, "Sidekick", move_payload, timeout=60)
            time.sleep(.25)
            if not move_response or move_response.status != 'SUCCESS':
                print(f"  - WARNING: Failed to move to y={y_pos}. Skipping measurement.")
                continue
            
            print(f"➡️  - Move complete. Taking measurement.")

            read_payload = {"func": "read", "args": {}}
            read_response = send_command_and_wait(colorimeter_postman, "Colorimeter", read_payload, valid_statuses=("DATA_RESPONSE", "PROBLEM"))
            time.sleep(1)
            if read_response and read_response.status == 'DATA_RESPONSE':
                

                intensity_list = read_response.payload.get('data',{})
                
                print(f"  - Measurement successful: {intensity_list}")
                
                measurement_dict = dict(zip(channel_names, intensity_list))
                
                row_data = {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'x_position': round(x_pos,3),
                    'y_position': round(y_pos,3)
                }
                row_data.update(measurement_dict)
                results_data.append(row_data)
            else:
                print(f"  - WARNING: Failed to get reading at y={y_pos}.")
        
        # 6. Post-Scan Cleanup
        print("\n[Step 6] Scan complete. Turning off colorimeter LED...")
        led_off_payload = {"func": "set", "args": {"led": False}}
        send_command_and_wait(colorimeter_postman, "Colorimeter", led_off_payload)
        
    except Exception as e:
        print(f"\nFATAL ERROR during workflow: {e}")
    finally:
        # 7. Write data to CSV and close connections
        if results_data:
            output_filename = "scan_results.csv"
            print(f"\n[Step 7] Saving {len(results_data)} data points to {output_filename}...")
            try:
                headers = results_data[0].keys()
                with open(output_filename, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(results_data)
                print("  - Save complete.")
            except Exception as e:
                print(f"  - ERROR: Could not save CSV file: {e}")

        print("\n[Step 8] Closing connections...")
        if sidekick_postman and sidekick_postman.is_open:
            sidekick_postman.close_channel()
            print("  - Sidekick connection closed.")
        if colorimeter_postman and colorimeter_postman.is_open:
            colorimeter_postman.close_channel()
            print("  - Colorimeter connection closed.")
        
    print("\n====== Scanning Experiment Script Finished ======")

if __name__ == "__main__":
    main()