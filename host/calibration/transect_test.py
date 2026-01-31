# host/calibration/transect_test.py
import sys
import time
import argparse
import json
from pathlib import Path
import queue
from datetime import datetime

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from host.core.device_manager import DeviceManager
from shared_lib.messages import Message
from host.firmware_db import get_device_name
from host.gui.console import C

def find_devices(manager: DeviceManager):
    """Scans for Sidekick and Colorimeter."""
    devices = {}
    print(f"{C.INFO}Scanning for devices...{C.END}")
    for dev_info in manager.scan_for_devices():
        name = get_device_name(dev_info['VID'], dev_info['PID']).lower()
        if 'sidekick' in name:
            devices['sidekick'] = dev_info['port']
        elif 'colorimeter' in name:
            devices['colorimeter'] = dev_info['port']
            
    if 'sidekick' in devices and 'colorimeter' in devices:
        print(f"{C.OK}Found Sidekick at {devices['sidekick']} and Colorimeter at {devices['colorimeter']}{C.END}")
        return devices
    else:
        print(f"{C.ERR}Could not find both devices.{C.END}")
        return None

def send_and_wait(manager, port, payload, wait_for_status="SUCCESS", timeout=30):
    """Sends a command and waits for a specific response status."""
    msg = Message("TRANSECT_SCRIPT", "INSTRUCTION", payload=payload)
    manager.send_message(port, msg)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            msg_type, msg_port, msg_data = manager.incoming_message_queue.get(timeout=0.1)
            if msg_port == port:
                if msg_data.status == wait_for_status:
                    return msg_data.payload
                elif msg_data.status == "PROBLEM":
                    print(f"{C.ERR}Device Problem: {msg_data.payload}{C.END}")
                    return None
        except queue.Empty:
            continue
    print(f"{C.ERR}Timeout waiting for {wait_for_status} on {port}{C.END}")
    return None

def get_current_steps(manager, sidekick_port):
    """Queries Sidekick for current absolute steps."""
    resp = send_and_wait(manager, sidekick_port, {"func": "get_info"}, "DATA_RESPONSE")
    if resp and 'data' in resp:
        return resp['data'].get('raw_motor_steps', {'m1': 0, 'm2': 0})
    return None

def move_to_absolute_steps(manager, port, target_m1, target_m2):
    """
    Calculates the relative delta needed to reach an absolute step position
    and executes the move using the 'steps' command.
    """
    current = get_current_steps(manager, port)
    if not current: return False

    d_m1 = int(target_m1) - int(current['m1'])
    d_m2 = int(target_m2) - int(current['m2'])
    
    if d_m1 == 0 and d_m2 == 0:
        return True

    # print(f"  -> Moving delta: {d_m1}, {d_m2}")
    return send_and_wait(manager, port, {"func": "steps", "args": {"m1": d_m1, "m2": d_m2}})

def run_transect(manager, sk_port, cm_port, axis, center_m1, center_m2, range_steps, step_size):
    """
    Performs a linear scan along one axis (m1 or m2) centered on the provided coordinates.
    Records ALL colorimetry data.
    """
    results = []
    
    # Generate offsets: -range ... 0 ... +range
    offsets = list(range(-range_steps, range_steps + 1, step_size))
    
    print(f"\n{C.INFO}Starting {axis.upper()} Transect around ({center_m1}, {center_m2})...{C.END}")
    
    for offset in offsets:
        # Calculate target position for this step
        target_m1 = center_m1 + (offset if axis == 'm1' else 0)
        target_m2 = center_m2 + (offset if axis == 'm2' else 0)
        
        # 1. Move Sidekick
        if not move_to_absolute_steps(manager, sk_port, target_m1, target_m2):
            print(f"{C.ERR}Move failed at offset {offset}. Aborting transect.{C.END}")
            break
            
        # 2. Measure Colorimeter
        # We wait for DATA_RESPONSE which contains the full spectrum
        resp = send_and_wait(manager, cm_port, {"func": "measure", "args": {}}, "DATA_RESPONSE")
        
        scan_data = {}
        if resp and 'data' in resp:
            scan_data = resp['data'] # This is the dictionary of all channels
        
        # Print a brief summary to console (e.g., Clear channel or Orange)
        # Assuming 'clear' or 'orange' exists in the map
        intensity_preview = scan_data.get('clear', 0)
        print(f"  Offset {offset:+4d} | M1:{target_m1} M2:{target_m2} | Clear:{intensity_preview}")
        
        results.append({
            "offset": offset,
            "m1": target_m1,
            "m2": target_m2,
            "spectral_data": scan_data
        })

    return results

def main():
    parser = argparse.ArgumentParser(description="Transect Test: Scans around a specific well.")
    parser.add_argument("well", type=str, help="Target well designation (e.g., A1, B12).")
    parser.add_argument("--range", type=int, default=10, help="Scan range +/- steps (default 10).")
    parser.add_argument("--step", type=int, default=1, help="Step size in steps (default 1).")
    parser.add_argument("--output", type=str, default=None, help="Output JSON filename.")
    args = parser.parse_args()

    # Generate default filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"transect_{args.well}_{timestamp}.json"

    manager = DeviceManager()
    manager.start()
    
    try:
        devs = find_devices(manager)
        if not devs: return

        sk = devs['sidekick']
        cm = devs['colorimeter']
        
        manager.connect_device(sk, 0, 0)
        manager.connect_device(cm, 0, 0)
        time.sleep(2) # Allow connections to stabilize

        # 1. Home
        print(f"\n{C.INFO}Homing Sidekick...{C.END}")
        if not send_and_wait(manager, sk, {"func": "home"}, timeout=30):
            print("Homing failed."); return

        # 2. Go to Well
        print(f"\n{C.INFO}Moving to target well: {args.well}...{C.END}")
        # Note: We do not pass a pump arg, so it defaults to 0 (end effector center)
        if not send_and_wait(manager, sk, {"func": "to_well", "args": {"well": args.well}}, timeout=20):
            print(f"Failed to reach well {args.well}."); return

        # 3. Get Baseline Steps (The "Center")
        center_coords = get_current_steps(manager, sk)
        if not center_coords:
            print("Failed to retrieve current steps."); return
            
        center_m1 = center_coords['m1']
        center_m2 = center_coords['m2']
        print(f"{C.OK}Reached {args.well} at steps: ({center_m1}, {center_m2}){C.END}")

        # 4. Perform M1 Transect
        m1_data = run_transect(manager, sk, cm, 'm1', center_m1, center_m2, args.range, args.step)

        # 5. Return to Center (Critical for M2 scan validity)
        print(f"\n{C.INFO}Returning to center ({center_m1}, {center_m2})...{C.END}")
        move_to_absolute_steps(manager, sk, center_m1, center_m2)

        # 6. Perform M2 Transect
        m2_data = run_transect(manager, sk, cm, 'm2', center_m1, center_m2, args.range, args.step)

        # 7. Save Data
        final_output = {
            "target_well": args.well,
            "center_steps": {"m1": center_m1, "m2": center_m2},
            "parameters": {"range": args.range, "step": args.step},
            "timestamp": datetime.now().isoformat(),
            "m1_transect": m1_data,
            "m2_transect": m2_data
        }

        with open(args.output, 'w') as f:
            json.dump(final_output, f, indent=2)
        print(f"\n{C.OK}Transect complete. Data saved to '{args.output}'{C.END}")

    except KeyboardInterrupt:
        print(f"\n{C.WARN}Aborted by user.{C.END}")
    except Exception as e:
        print(f"\n{C.ERR}Unexpected Error: {e}{C.END}")
    finally:
        manager.stop()

if __name__ == "__main__":
    main()