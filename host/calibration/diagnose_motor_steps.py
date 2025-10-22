# host/calibration/diagnose_motor_steps.py
import time
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path to allow importing project modules
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
    get_info_msg = Message(subsystem_name="HOST_DIAGNOSTIC", status="INSTRUCTION", payload={"func": "get_info"})
    manager.send_message(port, get_info_msg)
    start_time = time.time()
    while time.time() - start_time < 5: # 5-second timeout
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
    step_size = 5  # Start with medium step size
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
        
        # --- Handle Key Presses ---
        if char == 't':
            current_index = step_options.index(step_size)
            next_index = (current_index + 1) % len(step_options)
            step_size = step_options[next_index]
            print(f"\nSwitched to {step_size} motor steps.")
            continue

        if char in ('w', 's', 'a', 'd'):
            payload = {"func": "steps", "args": {}}
            if char == 'w': payload["args"] = {"m1": step_size, "m2": 0}
            elif char == 's': payload["args"] = {"m1": -step_size, "m2": 0}
            elif char == 'a': payload["args"] = {"m1": 0, "m2": step_size} # Note: A/D maps to M2
            elif char == 'd': payload["args"] = {"m1": 0, "m2": -step_size}
            
            print(f"Sent: {payload['args']}")
            msg = Message(subsystem_name="HOST_DIAGNOSTIC", status="INSTRUCTION", payload=payload)
            manager.send_message(port, msg)
            time.sleep(0.2) # Give a moment for the move

        elif char == '\r' or char == '\n':
            print("\nPosition confirmed.")
            return True

def main():
    """Main script execution."""
    print("====== Sidekick Motor Step Diagnostic Tool ======")
    print("This tool will help gather data on motor positioning accuracy.")
    
    manager = DeviceManager()
    manager.start()
    
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info:
        print("\nFATAL: Could not find a Sidekick device. Aborting.")
        manager.stop()
        return

    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        print(f"\nFATAL: Failed to connect to Sidekick on port {port}. Aborting.")
        manager.stop()
        return
        
    try:
        print("\nStep 1: Homing the Sidekick. This is essential for positioning.")
        manager.send_message(port, Message(subsystem_name="HOST_DIAGNOSTIC", status="INSTRUCTION", payload={"func": "home"}))
        time.sleep(10) # Ample time for homing and parking
        print("Homing complete.")

        diagnostic_data = []
        reference_wells = ['A1', 'A6', 'A12', 'D1', 'D6', 'D12', 'H1', 'H6', 'H12']

        for well in reference_wells:
            print(f"\n--- Diagnosing Well: {well} ---")
            
            # 1. Move to the device's predicted location for the well
            print(f"Moving pump 1 to the predicted location for well '{well}'...")
            # pump is easier to see, harder to back out the math (I think)
            #to_well_payload = {"func": "to_well", "args": {"well": well, "pump": "p1"}}
            to_well_payload = {"func": "to_well", "args": {"well": well}}
            manager.send_message(port, Message(subsystem_name="HOST_DIAGNOSTIC", status="INSTRUCTION", payload=to_well_payload))
            time.sleep(5) # Wait for the move to complete

            # 2. Get the initial motor steps
            initial_steps = get_device_motor_steps(manager, port)
            if not initial_steps or None in initial_steps:
                raise RuntimeError(f"Failed to get initial motor steps for {well}.")
            print(f"  -> Initial Motor Steps: (m1={initial_steps[0]}, m2={initial_steps[1]})")

            # 3. Allow user to jog to the actual position using motor steps
            interactive_motor_jog(manager, port, well)

            # 4. Get the final, user-corrected motor steps
            final_steps = get_device_motor_steps(manager, port)
            if not final_steps or None in final_steps:
                raise RuntimeError(f"Failed to get final (corrected) motor steps for {well}.")
            print(f"  -> Final Corrected Steps: (m1={final_steps[0]}, m2={final_steps[1]})")
            
            # 5. Store the data pair for the final report
            point_data = {
                "well": well,
                "initial_m1": initial_steps[0],
                "initial_m2": initial_steps[1],
                "final_m1": final_steps[0],
                "final_m2": final_steps[1]
            }
            diagnostic_data.append(point_data)
    
        print("\n\n" + "="*60)
        print("                 DIAGNOSIS COMPLETE")
        print("="*60)
        print("Here is the collected data. Please share this for evaluation.")
        print("-" * 60)
        for data in diagnostic_data:
            print(f"Well: {data['well']}")
            print(f"  Initial Steps -> (m1: {data['initial_m1']}, m2: {data['initial_m2']})")
            print(f"  Final Steps   -> (m1: {data['final_m1']}, m2: {data['final_m2']})")
            print("-" * 20)
 
        # === Save results to JSON file ===
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = Path(PROJECT_ROOT) / "calibration_data"
        save_dir.mkdir(exist_ok=True)

        out_file = save_dir / f"sidekick_calibration_{timestamp}.json"

        payload = {
            "timestamp": timestamp,
            "notes": "Motor step diagnostic data for 5-bar calibration",
            "arm_lengths_nominal_cm": {"L1": 7.0, "L2": 3.0, "L3": 10.0, "Ln": 0.5},
            "wells_tested": reference_wells,
            "data": diagnostic_data
        }

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"\nSaved diagnostic data to:\n  {out_file}")
        print("You can now run 'calibrate_fivebar.py' using this file.\n")

    except Exception as e:
        print(f"\nAn error occurred during the diagnostic process: {e}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()