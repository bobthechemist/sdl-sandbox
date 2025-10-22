# host/calibration/run_angle_calibration.py
import json
import time
import os
import sys
from datetime import datetime

try:
    import numpy as np
except ImportError:
    print("Error: The 'numpy' library is required. Run: pip install numpy")
    sys.exit(1)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from host.core.device_manager import DeviceManager
from shared_lib.messages import Message
from host.firmware_db import get_device_name

# (getch and find_sidekick_device helper functions would be included here as before)
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
    print("Scanning for connected devices...")
    for dev_info in manager.scan_for_devices():
        friendly_name = get_device_name(dev_info['VID'], dev_info['PID'])
        if 'sidekick' in friendly_name.lower():
            dev_info['friendly_name'] = friendly_name
            print(f"Found Sidekick ({friendly_name}) at {dev_info['port']}")
            return dev_info
    return None

def get_device_motor_angles(manager: DeviceManager, port: str):
    """Sends get_info and waits for the response to extract motor angles."""
    get_info_msg = Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "get_info"})
    manager.send_message(port, get_info_msg)
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            msg_type, msg_port, msg_data = manager.incoming_message_queue.get_nowait()
            if msg_port == port and msg_data.status == "DATA_RESPONSE":
                payload_data = msg_data.payload.get('data', {})
                if 'calculated_motor_angles_deg' in payload_data:
                    angles = payload_data['calculated_motor_angles_deg']
                    return (angles.get('theta1'), angles.get('theta2'))
        except Exception:
            time.sleep(0.1)
    print("\nError: Timed out waiting for angle response from device.")
    return None

def interactive_jog(manager: DeviceManager, port: str, well: str):
    """Provides a CLI for jogging the arm in Cartesian space."""
    # This function remains identical to the previous script
    step_size = 1.0
    print("\n" + "="*60)
    print(f" Interactive Jogging for Well '{well}' (Cartesian Control)")
    print("-"*60)
    print("  Use W/A/S/D to jog. [Enter] to confirm.")
    print("  [T] to toggle Coarse (1cm), Medium (0.1cm), and Fine (0.01cm) steps.")
    print(f"  Current Step Size: {step_size} cm")
    print("="*60)
    while True:
        char = getch().lower()
        if char == 't':
            if step_size == 1.0: step_size = 0.1
            elif step_size == 0.1: step_size = 0.01
            else: step_size = 1.0
            print(f"\nSwitched to {step_size} cm step size.")
            continue
        if char in ('w', 's', 'a', 'd'):
            payload = {"func": "move_rel", "args": {}}
            if char == 'w': payload["args"] = {"dx": 0, "dy": step_size}
            elif char == 's': payload["args"] = {"dx": 0, "dy": -step_size}
            elif char == 'a': payload["args"] = {"dx": -step_size, "dy": 0}
            elif char == 'd': payload["args"] = {"dx": step_size, "dy": 0}
            print(f"Sent: {payload['args']}")
            msg = Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload=payload)
            manager.send_message(port, msg)
            time.sleep(0.5)
        elif char == '\r' or char == '\n':
            print("\nPosition confirmed.")
            return True

def calculate_angle_correction_matrix(points: list):
    """Calculates the affine transformation for motor angles."""
    A, B = [], []
    for p in points:
        t1_pred, t2_pred = p['predicted_angles']
        t1_actual, t2_actual = p['actual_angles']
        A.extend([[t1_pred, t2_pred, 1, 0, 0, 0], [0, 0, 0, t1_pred, t2_pred, 1]])
        B.extend([t1_actual, t2_actual])
    
    A, B = np.array(A), np.array(B)
    try:
        solution, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
        return solution.reshape(2, 3).tolist()
    except np.linalg.LinAlgError as e:
        print(f"FATAL: Linear algebra error: {e}")
        return None

def main():
    print("====== Sidekick ANGLE-BASED Calibration Wizard ======")
    manager = DeviceManager()
    manager.start()
    
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info:
        manager.stop()
        return

    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        manager.stop()
        return
        
    try:
        print("\nStep 1: Homing the Sidekick...")
        manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "home"}))
        time.sleep(20)
        print("Homing complete.")

        calibration_points = []
        reference_wells = ['A1', 'H1', 'H12']

        for well in reference_wells:
            print(f"\n--- Calibrating Well: {well} ---")
            
            print(f"Moving pump 1 to predicted location for '{well}'...")
            to_well_payload = {"func": "to_well", "args": {"well": well, "pump": "p1"}}
            manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload=to_well_payload))
            time.sleep(10)

            predicted_angles = get_device_motor_angles(manager, port)
            if not predicted_angles or None in predicted_angles:
                raise RuntimeError(f"Failed to get predicted angles for {well}.")
            print(f"  -> Device Predicted Angles (t1, t2): {predicted_angles}")

            interactive_jog(manager, port, well)

            actual_angles = get_device_motor_angles(manager, port)
            if not actual_angles or None in actual_angles:
                raise RuntimeError(f"Failed to get actual angles for {well}.")
            print(f"  -> User Corrected Angles (t1, t2): {actual_angles}")
            
            point_data = {
                "well_name": well,
                "predicted_angles": predicted_angles,
                "actual_angles": actual_angles
            }
            calibration_points.append(point_data)
    
        print("\nStep 3: Calculating ANGLE correction matrix...")
        transform_matrix = calculate_angle_correction_matrix(calibration_points)
        if transform_matrix is None:
            raise RuntimeError("Matrix calculation failed.")

        final_calibration = {
            "calibration_date": datetime.utcnow().isoformat() + "Z",
            "method": "interactive_3_point_angle_correction",
            "reference_points": calibration_points,
            "transformation_matrix": transform_matrix
        }

        output_filename = "sidekick_calibration.json" # Same filename is fine
        with open(output_filename, 'w') as f:
            json.dump(final_calibration, f, indent=4)

        print("\n" + "="*50)
        print(" ANGLE CALIBRATION COMPLETE!")
        print(f" Saved angle calibration data to '{output_filename}'")
        print("\n Manually copy this file to the Sidekick's CIRCUITPY drive.")
        print("="*50)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()