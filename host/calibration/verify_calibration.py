# host/calibration/verify_calibration.py
import json
import time
import os
import sys
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

try:
    import numpy as np
except ImportError:
    print("Error: The 'numpy' library is required. Run: pip install numpy")
    sys.exit(1)

from host.core.device_manager import DeviceManager
from shared_lib.messages import Message
from host.firmware_db import get_device_name
from host.gui.console import C

def find_sidekick_device(manager: DeviceManager):
    # (This function is identical to the one in the calibration script)
    print(f"{C.INFO}Scanning for connected devices...{C.END}")
    for dev_info in manager.scan_for_devices():
        friendly_name = get_device_name(dev_info['VID'], dev_info['PID'])
        if 'sidekick' in friendly_name.lower():
            dev_info['friendly_name'] = friendly_name
            print(f"{C.OK}Found Sidekick ({friendly_name}) at {dev_info['port']}{C.END}")
            return dev_info
    return None

def main():
    """Main script to test the calibration file."""
    print(f"{C.OK}====== Sidekick Calibration Verification Tool ======{C.END}")
    
    # --- Load Calibration Data ---
    calibration_filename = PROJECT_ROOT / "host" / "calibration" / "quadratic_calibration.json"
    try:
        with open(calibration_filename, 'r') as f:
            cal_data = json.load(f)
        
        coeffs_m1 = cal_data["coefficients"]["motor1"]
        coeffs_m2 = cal_data["coefficients"]["motor2"]
        plate_info = cal_data["plate"]
        print(f"{C.OK}Successfully loaded calibration from '{calibration_filename}'{C.END}")
    except FileNotFoundError:
        print(f"{C.ERR}FATAL: Calibration file not found at '{calibration_filename}'{C.END}")
        print("Please run 'run_quadratic_calibration.py' first.")
        return
        
    # --- Define Helper Functions using loaded data ---
    def well_to_xy(well: str) -> tuple[float, float] | None:
        well = well.strip().upper()
        match = re.match(r'^([' + plate_info["rows"] + '])([1-9]|1[0-2])$', well)
        if not match: return None
        row_idx = plate_info["rows"].find(match.group(1))
        col_idx = int(match.group(2)) - 1
        return (col_idx * plate_info["well_pitch_cm"], row_idx * plate_info["well_pitch_cm"])

    def xy_to_steps(x: float, y: float) -> tuple[int, int]:
        features = np.array([1, x, y, x**2, x*y, y**2])
        m1 = np.dot(features, coeffs_m1)
        m2 = np.dot(features, coeffs_m2)
        return (int(round(m1)), int(round(m2)))

    # --- Connect to Device ---
    manager = DeviceManager()
    manager.start()
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info: manager.stop(); return
    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        manager.stop(); return
        
    try:
        print(f"\n{C.INFO}Homing the Sidekick...{C.END}")
        manager.send_message(port, Message(subsystem_name="HOST_VERIFIER", status="INSTRUCTION", payload={"func": "home"}))
        time.sleep(15)
        print(f"{C.OK}Homing complete.{C.END}")

        while True:
            print("\n" + "="*50)
            well_str = input("Enter target well (e.g., 'B7', 'G11') or 'q' to quit: ")
            if well_str.lower() == 'q':
                break
            
            xy_coords = well_to_xy(well_str)
            if xy_coords is None:
                print(f"{C.ERR}Invalid well format. Please try again.{C.END}")
                continue
            
            target_steps = xy_to_steps(xy_coords[0], xy_coords[1])
            print(f"  -> Calculated Target Steps: {C.INFO}{target_steps}{C.END}")
            
            # Use the 'to_well' command on the device, which should now use the same logic
            move_payload = {"func": "to_well", "args": {"well": well_str}}
            move_msg = Message(subsystem_name="HOST_VERIFIER", status="INSTRUCTION", payload=move_payload)
            manager.send_message(port, move_msg)
            print("  -> Sent 'to_well' command. Observe the physical device.")
            time.sleep(5)

    except Exception as e:
        print(f"\n{C.ERR}An error occurred: {e}{C.END}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()