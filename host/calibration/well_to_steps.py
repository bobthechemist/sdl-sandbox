# host/calibration/create_well_to_step_map.py
import time
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path to allow importing project modules
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

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
    print(f"\n{C.ERR}Error: Timed out waiting for motor step response from device.{C.END}")
    return None

def interactive_motor_jog(manager: DeviceManager, port: str, well: str):
    """Provides a CLI interface for jogging motors directly using steps."""
    step_size = 5
    step_options = [1, 5, 20] # Fine, Medium, Coarse
    
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
            next_index = (current_index + 1) % len(step_options)
            step_size = step_options[next_index]
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
    """Main script execution."""
    print(f"{C.OK}====== Sidekick Well-to-Step Mapping Wizard ======{C.END}")
    
    manager = DeviceManager()
    manager.start()
    
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info:
        print(f"\n{C.ERR}FATAL: Could not find a Sidekick device. Aborting.{C.END}")
        manager.stop()
        return

    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        print(f"\n{C.ERR}FATAL: Failed to connect to Sidekick on port {port}. Aborting.{C.END}")
        manager.stop()
        return
        
    try:
        print(f"\n{C.INFO}Step 1: Homing the Sidekick. This may take a moment...{C.END}")
        manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload={"func": "home"}))
        time.sleep(15) # Ample time for homing and parking
        print(f"{C.OK}Homing complete.{C.END}")

        final_well_map = {}
        # The 9 reference wells you requested
        reference_wells = ['A1', 'A6', 'A12', 'E1', 'E6', 'E12', 'H1', 'H6', 'H12']

        for well in reference_wells:
            print(f"\n--- Calibrating Well: {C.WARN}{well}{C.END} ---")
            
            print(f"Moving to the approximate location for well '{well}'...")
            to_well_payload = {"func": "to_well", "args": {"well": well}}
            manager.send_message(port, Message(subsystem_name="HOST_CALIBRATOR", status="INSTRUCTION", payload=to_well_payload))
            time.sleep(5) 

            # Allow user to jog to the precise position
            interactive_motor_jog(manager, port, well)

            # Get the final, user-corrected motor steps
            final_steps = get_device_motor_steps(manager, port)
            if not final_steps or None in final_steps:
                raise RuntimeError(f"Failed to get final (corrected) motor steps for {well}.")
            
            final_m1, final_m2 = final_steps
            print(f"  -> {C.OK}Logged Steps for {well}: (m1: {final_m1}, m2: {final_m2}){C.END}")
            
            # Store the data for the final map
            final_well_map[well] = [final_m1, final_m2]
    
        print("\n\n" + "="*60)
        print(f"{C.OK}                 CALIBRATION COMPLETE{C.END}")
        print("="*60)
 
        # --- Save results to a new JSON file ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = Path(PROJECT_ROOT) / "host" / "calibration"
        save_dir.mkdir(exist_ok=True)

        out_file = save_dir / "sidekick_well_map.json"

        payload = {
            "calibration_date": datetime.utcnow().isoformat() + "Z",
            "method": "9_point_well_to_step_mapping",
            "well_map": final_well_map
        }

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)

        print(f"\n{C.OK}Saved well-to-step mapping data to:{C.END}\n  {out_file}")
        print(f"\n{C.WARN}NEXT STEP: Copy this '{out_file.name}' file to the Sidekick's CIRCUITPY drive.{C.END}\n")

    except Exception as e:
        print(f"\n{C.ERR}An error occurred during the process: {e}{C.END}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()