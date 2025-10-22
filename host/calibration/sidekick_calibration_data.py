# host/calibration/run_xy_to_step_calibration.py
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

# Add the project root to the Python path to allow importing project modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from host.core.device_manager import DeviceManager
from shared_lib.messages import Message
from host.firmware_db import get_device_name

# --- Constants that MUST match the firmware configuration ---
# These are taken from firmware/sidekick/__init__.py
A1_OFFSET_DX = 7.24
A1_OFFSET_DY = -5.57
WELL_SPACING_CM = 0.9

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

def get_device_motor_steps(manager: DeviceManager, port: str):
    """Sends get_info and waits for the response to extract raw motor steps."""
    get_info_msg = Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "get_info"})
    manager.send_message(port, get_info_msg)
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            msg_type, msg_port, msg_data = manager.incoming_message_queue.get_nowait()
            if msg_port == port and msg_data.status == "DATA_RESPONSE":
                payload_data = msg_data.payload.get('data', {})
                if 'raw_motor_steps' in payload_data:
                    steps = payload_data['raw_motor_steps']
                    return (steps.get('m1'), steps.get('m2'))
        except Exception:
            time.sleep(0.1)
    print("\nError: Timed out waiting for motor step response from device.")
    return None

def interactive_motor_jog(manager: DeviceManager, port: str, well: str):
    """Provides a CLI interface for jogging motors directly using steps."""
    step_size = 5
    step_options = [2, 5, 10]
    print("\n" + "="*60)
    print(f" Interactive Motor Jogging for Well '{well}'")
    print("-"*60)
    print("  [W]/[S]: Nudge Motor 1 (+/-) | [A]/[D]: Nudge Motor 2 (+/-)")
    print("  [T] to cycle step size | [Enter] to confirm position.")
    print(f"  Current Step Size: {step_size} steps")
    print("="*60)
    while True:
        char = getch().lower()
        if char == 't':
            current_index = step_options.index(step_size)
            step_size = step_options[(current_index + 1) % len(step_options)]
            print(f"\nSwitched to {step_size} motor steps.")
            continue
        if char in ('w', 's', 'a', 'd'):
            payload = {"func": "steps", "args": {}}
            if char == 'w': payload["args"] = {"m1": step_size, "m2": 0}
            elif char == 's': payload["args"] = {"m1": -step_size, "m2": 0}
            elif char == 'a': payload["args"] = {"m1": 0, "m2": step_size}
            elif char == 'd': payload["args"] = {"m1": 0, "m2": -step_size}
            print(f"Sent: {payload['args']}")
            msg = Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload=payload)
            manager.send_message(port, msg)
            time.sleep(0.2)
        elif char == '\r' or char == '\n':
            print("\nPosition confirmed.")
            return True

def well_to_coords(well_designation: str):
    """Translates a well designation into theoretical (X, Y) coordinates."""
    sanitized_well = well_designation.upper().strip()
    match = re.match(r'^([A-H])([1-9]|1[0-2])$', sanitized_well)
    if not match: return None
    letter_part, number_part = match.group(1), int(match.group(2))
    row_index = ord(letter_part) - ord('A')
    col_index = number_part - 1
    
    # NOTE: This calculation has been corrected to match standard plate layouts.
    # Rows (A-H) correspond to the Y-axis, Columns (1-12) to the X-axis.
    x_coord = A1_OFFSET_DX + (col_index * WELL_SPACING_CM)
    y_coord = A1_OFFSET_DY + (row_index * WELL_SPACING_CM)
    return (x_coord, y_coord)

def calculate_xy_to_step_matrix(points: list):
    """Calculates the affine transformation from world (x,y) to motor (m1,m2)."""
    A, B = [], []
    for p in points:
        x, y = p['goal_coords_cm']
        m1, m2 = p['final_motor_steps']
        A.extend([[x, y, 1, 0, 0, 0], [0, 0, 0, x, y, 1]])
        B.extend([m1, m2])
    A, B = np.array(A), np.array(B)
    try:
        solution, _, rank, _ = np.linalg.lstsq(A, B, rcond=None)
        if rank < 6:
            print("Warning: Reference points may be collinear, leading to poor calibration.")
        return solution.reshape(2, 3).tolist()
    except np.linalg.LinAlgError as e:
        print(f"FATAL: Linear algebra error: {e}")
        return None

def main():
    """Main script execution."""
    print("====== Sidekick Direct XY-to-Step Calibration Wizard ======")
    manager = DeviceManager()
    manager.start()
    
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info:
        manager.stop(); return

    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        manager.stop(); return
        
    try:
        print("\nStep 1: Homing the Sidekick...")
        manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "home"}))
        time.sleep(20)
        print("Homing complete.")

        calibration_points = []
        reference_wells = ['A1', 'H1', 'H12']

        for well in reference_wells:
            print(f"\n--- Calibrating Well: {well} ---")
            
            goal_coords = well_to_coords(well)
            if goal_coords is None:
                raise ValueError(f"Could not parse well designation {well}")
            print(f"  -> Theoretical Goal (x,y): {goal_coords}")

            print(f"Moving pump 1 to the device's current best-guess for '{well}'...")
            to_well_payload = {"func": "to_well", "args": {"well": well, "pump": "p1"}}
            manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload=to_well_payload))
            time.sleep(10)

            interactive_motor_jog(manager, port, well)

            final_steps = get_device_motor_steps(manager, port)
            if not final_steps or None in final_steps:
                raise RuntimeError(f"Failed to get final motor steps for {well}.")
            print(f"  -> Final Corrected Steps (m1, m2): {final_steps}")
            
            point_data = {
                "well": well,
                "goal_coords_cm": goal_coords,
                "final_motor_steps": final_steps
            }
            calibration_points.append(point_data)
    
        print("\nStep 3: Calculating the XY -> Step transformation matrix...")
        transform_matrix = calculate_xy_to_step_matrix(calibration_points)
        if transform_matrix is None:
            raise RuntimeError("Matrix calculation failed.")

        final_calibration = {
            "calibration_date": datetime.utcnow().isoformat() + "Z",
            "method": "interactive_3_point_xy_to_step_mapping",
            "reference_points": calibration_points,
            "transformation_matrix": transform_matrix
        }

        output_filename = "sidekick_calibration.json"
        with open(output_filename, 'w') as f:
            json.dump(final_calibration, f, indent=4)

        print("\n" + "="*50)
        print(" CALIBRATION COMPLETE!")
        print(f" Successfully saved calibration data to '{output_filename}'")
        print("\n You can now manually copy this file to the Sidekick's CIRCUITPY drive.")
        print("="*50)

    except Exception as e:
        print(f"\nAn error occurred during the calibration process: {e}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()