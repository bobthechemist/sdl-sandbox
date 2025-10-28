# host/calibration/run_quadratic_calibration.py
import time
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path to allow importing project modules
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
    print(f"{C.INFO}Scanning for connected devices...{C.END}")
    for dev_info in manager.scan_for_devices():
        friendly_name = get_device_name(dev_info['VID'], dev_info['PID'])
        if 'sidekick' in friendly_name.lower():
            dev_info['friendly_name'] = friendly_name
            print(f"{C.OK}Found Sidekick ({friendly_name}) at {dev_info['port']}{C.END}")
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
    print(f"\n{C.ERR}Error: Timed out waiting for motor step response.{C.END}")
    return None

def interactive_motor_jog(manager: DeviceManager, port: str, well: str):
    """Provides a CLI interface for jogging motors directly using steps."""
    step_size = 5
    step_options = [1, 5, 20]  # Fine, Medium, Coarse
    print("\n" + "="*60)
    print(f" Interactive Motor Jogging for Well '{well}'")
    print("-"*60)
    print("  [W]/[S]: Nudge Motor 1 (+/-) | [A]/[D]: Nudge Motor 2 (+/-)")
    print("  [T] to cycle step size | [Enter] to confirm position.")
    print(f"  Current Step Size: {C.INFO}{step_size} steps{C.END}")
    print("="*60)
    while True:
        char = getch().lower()
        if char == 't':
            current_index = step_options.index(step_size)
            step_size = step_options[(current_index + 1) % len(step_options)]
            print(f"\nSwitched to {C.INFO}{step_size}{C.END} motor steps.")
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
            print(f"\n{C.OK}Position confirmed for {well}.{C.END}")
            return True

def main():
    """Main script to collect data and generate the quadratic calibration file."""
    print(f"{C.OK}====== Sidekick Quadratic Calibration Wizard ======{C.END}")
    manager = DeviceManager()
    manager.start()
    
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info:
        manager.stop(); return

    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        manager.stop(); return
        
    try:
        # --- PART 1: DATA COLLECTION ---
        print(f"\n{C.INFO}Step 1: Homing the Sidekick...{C.END}")
        manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "home"}))
        time.sleep(15)
        print(f"{C.OK}Homing complete.{C.END}")

        collected_steps = []
        collected_xy = []
        reference_wells = ['A1', 'A6', 'A12', 'E1', 'E6', 'E12', 'H1', 'H6', 'H12']
        plate_pitch_cm = 0.9

        for well in reference_wells:
            print(f"\n--- Calibrating Well: {C.WARN}{well}{C.END} ---")
            
            # Convert well name to XY coordinate for the data matrix
            row_idx = "ABCDEFGH".find(well[0])
            col_idx = int(well[1:]) - 1
            x_coord = col_idx * plate_pitch_cm
            y_coord = row_idx * plate_pitch_cm
            collected_xy.append([x_coord, y_coord])
            
            # Go to approximate location
            print(f"Moving to approximate location for '{well}'...")
            to_well_payload = {"func": "to_well", "args": {"well": well}}
            manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload=to_well_payload))
            time.sleep(5) 
            
            # Interactive Jogging
            interactive_motor_jog(manager, port, well)
            final_steps = get_device_motor_steps(manager, port)
            if not final_steps: raise RuntimeError(f"Failed to get motor steps for {well}.")
            
            collected_steps.append(list(final_steps))
            print(f"  -> {C.OK}Logged Steps for {well}: (m1: {final_steps[0]}, m2: {final_steps[1]}){C.END}")
        
        # --- PART 2: COEFFICIENT CALCULATION ---
        print(f"\n{C.INFO}Step 2: Calculating quadratic coefficients...{C.END}")
        XY = np.array(collected_xy)
        steps = np.array(collected_steps)
        x, y = XY[:, 0], XY[:, 1]
        
        # Build quadratic design matrix: [1, x, y, x^2, xy, y^2]
        A = np.column_stack([np.ones_like(x), x, y, x**2, x*y, y**2])
        
        coeffs, _, _, _ = np.linalg.lstsq(A, steps, rcond=None)
        
        # --- PART 3: SAVE THE CALIBRATION FILE ---
        print(f"{C.INFO}Step 3: Saving calibration file...{C.END}")
        calibration_data = {
            "calibration_date": datetime.utcnow().isoformat() + "Z",
            "method": "9_point_quadratic_xy_to_steps",
            "coefficients": {
                "motor1": coeffs[:, 0].tolist(),
                "motor2": coeffs[:, 1].tolist()
            },
            "plate": {
                "well_pitch_cm": plate_pitch_cm,
                "rows": "ABCDEFGH",
                "columns": 12
            }
        }
        
        out_file = PROJECT_ROOT / "host" / "calibration" / "quadratic_calibration.json"
        with open(out_file, "w") as f:
            json.dump(calibration_data, f, indent=2)

        print("\n\n" + "="*60)
        print(f"{C.OK}                 CALIBRATION COMPLETE{C.END}")
        print("="*60)
        print(f"\n{C.OK}Saved quadratic calibration data to:{C.END}\n  {out_file}")
        print(f"\n{C.WARN}NEXT STEP: Copy this file to the Sidekick's CIRCUITPY drive.{C.END}\n")

    except Exception as e:
        print(f"\n{C.ERR}An error occurred: {e}{C.END}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()