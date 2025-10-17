import json
import time
import os
import sys
import re  # <-- NEW: Import the regular expression module

try:
    import numpy as np
except ImportError:
    print("Error: The 'numpy' library is required for this script.")
    print("Please install it by running: pip install numpy")
    sys.exit(1)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from host.core.device_manager import DeviceManager
from shared_lib.messages import Message
from host.firmware_db import get_device_name

# ==============================================================================
# NEW HELPER FUNCTION
# ==============================================================================
def well_to_coords(well_designation: str, spacing_cm: float = 0.9):
    """
    Translates a standard well plate designation (e.g., 'A1', 'H12') into
    (X, Y) coordinates in centimeters, assuming A1 is at (0, 0).

    Args:
        well_designation (str): The well identifier (e.g., "C7").
        spacing_cm (float): The center-to-center distance between wells.

    Returns:
        tuple[float, float] | None: A tuple of (x, y) coordinates or None if the
                                    designation is invalid.
    """
    # Sanitize and validate the input format using a regular expression
    sanitized_well = well_designation.upper().strip()
    match = re.match(r'^([A-H])([1-9]|1[0-2])$', sanitized_well)

    if not match:
        print(f"  -> ERROR: Invalid well designation '{well_designation}'. Must be a letter A-H followed by a number 1-12.")
        return None

    # Extract the letter (row) and number (column)
    letter_part = match.group(1)
    number_part = int(match.group(2))

    # 'A' corresponds to index 0, 'B' to 1, etc.
    # ord(letter) gets the ASCII value. ord('A') is the offset.
    x_index = ord(letter_part) - ord('A')
    
    # '1' corresponds to index 0, '2' to 1, etc.
    y_index = number_part - 1
    
    # Calculate the final coordinates
    x_coord = x_index * spacing_cm
    y_coord = y_index * spacing_cm
    
    return (x_coord, y_coord)


def find_sidekick_device(manager: DeviceManager):
    """Scans for devices and returns the info for the first Sidekick found."""
    print("Scanning for connected devices...")
    devices = manager.scan_for_devices()
    for dev_info in devices:
        friendly_name = get_device_name(dev_info['VID'], dev_info['PID'])
        if 'sidekick' in friendly_name.lower():
            dev_info['friendly_name'] = friendly_name
            print(f"Found Sidekick ({friendly_name}) at {dev_info['port']}")
            return dev_info
    return None

def get_current_steps(manager: DeviceManager, port: str):
    """Sends get_info and waits for a DATA_RESPONSE to get current motor steps."""
    get_info_msg = Message(subsystem_name="HOST_TESTER", status="INSTRUCTION", payload={"func": "get_info", "args": {}})
    manager.send_message(port, get_info_msg)
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            msg_type, msg_port, msg_data = manager.incoming_message_queue.get_nowait()
            if msg_port == port and msg_data.status == "DATA_RESPONSE":
                payload_data = msg_data.payload.get('data', {})
                if 'm1_steps' in payload_data and 'm2_steps' in payload_data:
                    return (payload_data['m1_steps'], payload_data['m2_steps'])
        except Exception:
            time.sleep(0.1)
    return None

def apply_transform_inverse(transform_matrix, world_coords_cm):
    """
    Solves the inverse problem: given (x, y), find (m1, m2).
    """
    x, y = world_coords_cm
    a, b, c = transform_matrix[0]
    d, e, f = transform_matrix[1]
    A = np.array([[a, b], [d, e]])
    B = np.array([x - c, y - f])
    
    try:
        motor_coords = np.linalg.solve(A, B)
        return (int(round(motor_coords[0])), int(round(motor_coords[1])))
    except np.linalg.LinAlgError:
        print("Error: Could not solve for motor coordinates. The calibration matrix may be singular.")
        return None

def main():
    """Main script to test the calibration file."""
    calibration_filename = "sidekick_calibration.json"
    
    try:
        with open(calibration_filename, 'r') as f:
            calibration_data = json.load(f)
        transform_matrix = calibration_data['transformation_matrix']
        print(f"Successfully loaded calibration data from '{calibration_filename}'")
    except FileNotFoundError:
        print(f"FATAL: Calibration file '{calibration_filename}' not found.")
        print("Please run the 'run_sidekick_calibration.py' script first.")
        return
        
    manager = DeviceManager()
    manager.start()
    
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info:
        print("\nFATAL: Could not find a Sidekick device.")
        manager.stop()
        return

    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        print(f"\nFATAL: Failed to connect to Sidekick on port {port}.")
        manager.stop()
        return
        
    try:
        print("\nHoming the Sidekick... (this is essential for testing)")
        home_msg = Message(subsystem_name="HOST_TESTER", status="INSTRUCTION", payload={"func": "home", "args": {}})
        manager.send_message(port, home_msg)
        time.sleep(15)
        print("Homing complete.")

        # ==============================================================================
        # MODIFIED MAIN LOOP
        # ==============================================================================
        while True:
            print("\n" + "="*50)
            well_str = input("Enter target well plate designation (e.g., 'A1', 'H12') or 'q' to quit: ")
            if well_str.lower() == 'q':
                break
            
            # 1. Translate well designation to coordinates
            target_coords_cm = well_to_coords(well_str)
            if target_coords_cm is None:
                # The helper function already printed an error message.
                continue
            
            target_x, target_y = target_coords_cm
            print(f"  -> Translating '{well_str.upper().strip()}' to coordinates: ({target_x:.2f}, {target_y:.2f}) cm")
            
            # --- The rest of the logic is the same as before ---
            
            # 2. Convert world coords to target motor steps
            target_motor_steps = apply_transform_inverse(transform_matrix, (target_x, target_y))
            if target_motor_steps is None:
                continue
            
            target_m1, target_m2 = target_motor_steps
            print(f"  -> Calculated Target Motor Steps: ({target_m1}, {target_m2})")

            # 3. Get the device's current position
            current_motor_steps = get_current_steps(manager, port)
            if current_motor_steps is None:
                print("  -> ERROR: Failed to get current position from device.")
                continue
            
            current_m1, current_m2 = current_motor_steps
            print(f"  -> Current Motor Steps: ({current_m1}, {current_m2})")
            
            # 4. Calculate the relative move
            rel_m1 = target_m1 - current_m1
            rel_m2 = target_m2 - current_m2
            print(f"  -> Calculated Relative Move: ({rel_m1}, {rel_m2})")
            
            # 5. Send the 'steps' command
            move_payload = {"func": "steps", "args": {"m1": rel_m1, "m2": rel_m2}}
            move_msg = Message(subsystem_name="HOST_TESTER", status="INSTRUCTION", payload=move_payload)
            manager.send_message(port, move_msg)
            print("  -> Sent move command. Observe the physical device.")
            
            time.sleep(5)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()