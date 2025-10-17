import json
import time
import os
import sys
from datetime import datetime
import re

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

# --- Helper for Cross-Platform Single-Key Input ---
try:
    import msvcrt
    def getch():
        return msvcrt.getch().decode('utf-8')
except ImportError:
    import tty
    import termios
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def well_to_coords(well_designation: str, spacing_cm: float = 0.9):
    """Translates a standard well plate designation into (X, Y) coordinates."""
    sanitized_well = well_designation.upper().strip()
    match = re.match(r'^([A-H])([1-9]|1[0-2])$', sanitized_well)
    if not match:
        print(f"  -> ERROR: Invalid well designation '{well_designation}'. Must be A-H followed by 1-12.")
        return None
    letter_part, number_part = match.group(1), int(match.group(2))
    x_index = ord(letter_part) - ord('A')
    y_index = number_part - 1
    return (x_index * spacing_cm, y_index * spacing_cm)

def find_sidekick_device(manager: DeviceManager):
    """Scans for devices and returns the info for the first Sidekick found."""
    print("Scanning for connected devices...")
    for dev_info in manager.scan_for_devices():
        friendly_name = get_device_name(dev_info['VID'], dev_info['PID'])
        if 'sidekick' in friendly_name.lower():
            dev_info['friendly_name'] = friendly_name
            print(f"Found Sidekick ({friendly_name}) at {dev_info['port']}")
            return dev_info
    return None

# ==============================================================================
# REVISED HELPER FUNCTION (was get_current_steps)
# ==============================================================================
def get_device_status_info(manager: DeviceManager, port: str):
    """Sends get_info and waits for the full DATA_RESPONSE payload."""
    get_info_msg = Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "get_info"})
    manager.send_message(port, get_info_msg)
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            msg_type, msg_port, msg_data = manager.incoming_message_queue.get_nowait()
            if msg_port == port and msg_data.status == "DATA_RESPONSE" and "device_calculated_cartesian_cm" in msg_data.payload.get('data', {}):
                return msg_data.payload.get('data')
        except Exception:
            time.sleep(0.1)
    print("\nError: Timed out waiting for get_info response from device.")
    return None

# ==============================================================================
# REVISED JOG FUNCTION
# ==============================================================================
def interactive_jog(manager: DeviceManager, port: str, point_number: int):
    """Provides a CLI interface for jogging the motors, with a get_info key."""
    jog_step = 10
    print("\n" + "="*50)
    print(f" Interactive Jogging Mode for Reference Point #{point_number}")
    print("-"*50)
    print("  [W]/[S]: Nudge M1 | [A]/[D]: Nudge M2 | [G]: Get Status Info")
    print("\n  Press [Enter] to confirm the position.")
    print("="*50)

    while True:
        char = getch().lower()
        
        # --- Handle Key Presses ---
        if char in ('w', 's', 'a', 'd'):
            payload = {"func": "steps", "args": {}}
            if char == 'w': payload["args"] = {"m1": jog_step, "m2": 0}
            elif char == 's': payload["args"] = {"m1": -jog_step, "m2": 0}
            elif char == 'a': payload["args"] = {"m1": 0, "m2": jog_step}
            elif char == 'd': payload["args"] = {"m1": 0, "m2": -jog_step}
            print(f"Sent: {payload['args']}")
            msg = Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload=payload)
            manager.send_message(port, msg)

        elif char == 'g':
            print("\nRequesting device status...")
            status_info = get_device_status_info(manager, port)
            if status_info:
                print("-" * 20)
                # Pretty print the received dictionary
                print(json.dumps(status_info, indent=2))
                print("-" * 20)
            # Re-print the prompt
            print("\n[W]/[S]: M1 | [A]/[D]: M2 | [G]: Get Info | [Enter]: Confirm")

        elif char == '\r' or char == '\n':
            print("\nPosition confirmed. Fetching final motor step counts...")
            final_status = get_device_status_info(manager, port)
            if final_status:
                motor_steps = final_status.get('raw_motor_steps', {})
                m1 = motor_steps.get('m1')
                m2 = motor_steps.get('m2')
                if m1 is not None and m2 is not None:
                    return (m1, m2)
            print("Error: Could not retrieve final step counts.")
            return None # Indicate failure
        
        # Short delay to prevent spamming the device
        time.sleep(0.1)


def get_world_coords_from_well(point_number: int):
    """Prompts the user to enter a well designation and converts it to coordinates."""
    while True:
        well_str = input(f"Enter the WELL DESIGNATION for Reference Point #{point_number} (e.g., 'A1', 'H12'): ")
        coords = well_to_coords(well_str)
        if coords is not None:
            return coords

def calculate_transformation(points: list):
    """Calculates the affine transformation matrix."""
    A, B = [], []
    for p in points:
        m1, m2 = p['motor_coords']
        x, y = p['world_coords_cm']
        A.extend([[m1, m2, 1, 0, 0, 0], [0, 0, 0, m1, m2, 1]])
        B.extend([x, y])
    A, B = np.array(A), np.array(B)
    try:
        solution, _, rank, _ = np.linalg.lstsq(A, B, rcond=None)
        if rank < 6:
            print("Warning: The reference points may be collinear, potentially leading to an inaccurate calibration.")
        return solution.reshape(2, 3).tolist()
    except np.linalg.LinAlgError as e:
        print(f"FATAL: Linear algebra error: {e}")
        return None

def main():
    """Main script execution."""
    print("====== Sidekick 3-Point Well Plate Calibration Wizard ======")
    print("INFO: For best results, choose 3 non-collinear points (e.g., A1, H1, A12).")

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
        print("\nStep 1: Homing the Sidekick. Please wait...")
        manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "home"}))
        time.sleep(15)
        print("Homing complete.")

        calibration_points = []
        for i in range(1, 4):
            motor_coords = interactive_jog(manager, port, i)
            if motor_coords is None:
                raise RuntimeError(f"Failed to get motor coordinates for Point #{i}.")
            
            world_coords = get_world_coords_from_well(i)
            
            point_data = {
                "motor_coords": motor_coords,
                "world_coords_cm": world_coords
            }
            calibration_points.append(point_data)
            print(f"  -> Stored Point #{i}: motor={motor_coords}, world_well={world_coords}")
    
        print("\nStep 3: Calculating transformation matrix...")
        transform_matrix = calculate_transformation(calibration_points)
        if transform_matrix is None:
            raise RuntimeError("Failed to calculate transformation matrix.")

        final_calibration = {
            "calibration_date": datetime.utcnow().isoformat() + "Z",
            "method": "user_guided_3_point_well_plate",
            "reference_points": calibration_points,
            "transformation_matrix": transform_matrix
        }

        output_filename = "sidekick_calibration.json"
        with open(output_filename, 'w') as f:
            json.dump(final_calibration, f, indent=4)

        print("\n" + "="*50)
        print(" CALIBRATION COMPLETE!")
        print(f" Saved calibration data to '{output_filename}'")
        print("="*50)

    except Exception as e:
        print(f"\nAn error occurred during the calibration process: {e}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()