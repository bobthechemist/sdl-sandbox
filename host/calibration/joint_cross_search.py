import sys
import time
import argparse
import json
from pathlib import Path
import queue

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from host.core.device_manager import DeviceManager
from shared_lib.messages import Message
from host.firmware_db import get_device_name
from host.gui.console import C

def find_devices(manager: DeviceManager):
    devices = {}
    print(f"{C.INFO}Scanning for devices...{C.END}")
    for dev_info in manager.scan_for_devices():
        name = get_device_name(dev_info['VID'], dev_info['PID']).lower()
        if 'sidekick' in name:
            devices['sidekick'] = dev_info['port']
        elif 'colorimeter' in name:
            devices['colorimeter'] = dev_info['port']
    return devices

def send_and_wait(manager, port, payload, wait_for_status="SUCCESS", timeout=30):
    msg = Message("TEST_SCRIPT", "INSTRUCTION", payload=payload)
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

    # print(f"  -> Moving {d_m1}, {d_m2} steps...")
    return send_and_wait(manager, port, {"func": "steps", "args": {"m1": d_m1, "m2": d_m2}})

def scan_joint(manager, sk_port, cm_port, joint_name, start_m1, start_m2, range_steps, step_size):
    """
    Scans a single joint (m1 or m2) while holding the other fixed.
    Returns the list of data points.
    """
    results = []
    
    # Generate the list of target offsets relative to the center
    # e.g., if range=100, step=10 -> -100, -90, ... 0 ... 90, 100
    offsets = list(range(-range_steps, range_steps + 1, step_size))
    
    print(f"\n{C.INFO}Scanning {joint_name.upper()}... ({len(offsets)} points){C.END}")
    
    for offset in offsets:
        # Calculate target absolute positions
        target_m1 = start_m1 + (offset if joint_name == 'm1' else 0)
        target_m2 = start_m2 + (offset if joint_name == 'm2' else 0)
        
        # 1. Move
        if not move_to_absolute_steps(manager, sk_port, target_m1, target_m2):
            print("Move failed."); break
            
        # 2. Measure
        resp = send_and_wait(manager, cm_port, {"func": "measure", "args": {}}, "DATA_RESPONSE")
        intensity = 0
        if resp and 'data' in resp:
            intensity = resp['data'].get('orange', 0)
            
        print(f"  Offset {offset:+4d} | M1:{target_m1} M2:{target_m2} | Int:{intensity}")
        
        results.append({
            "offset": offset,
            "m1": target_m1,
            "m2": target_m2,
            "intensity": intensity
        })

    return results

def find_valley_center(data):
    """
    Identifies the best step position.
    Instead of just taking the single minimum, it takes the average of the
    bottom 3 points to handle noise, or just the min if the valley is sharp.
    """
    if not data: return None
    
    # Sort by intensity ascending
    sorted_data = sorted(data, key=lambda x: x['intensity'])
    
    # Get the single lowest point
    best_point = sorted_data[0]
    
    print(f"  -> Valley bottom found at intensity {best_point['intensity']} (Offset: {best_point['offset']})")
    
    # Return the absolute coordinates of the best point
    return best_point['m1'], best_point['m2']

def main():
    parser = argparse.ArgumentParser(description="Joint Space Cross Search")
    parser.add_argument("--m1", type=int, required=True, help="Starting M1 steps")
    parser.add_argument("--m2", type=int, required=True, help="Starting M2 steps")
    parser.add_argument("--range", type=int, default=200, help="Scan range +/- steps (default 200)")
    parser.add_argument("--step", type=int, default=10, help="Step size steps (default 10)")
    parser.add_argument("--output", type=str, default="joint_search_result.json")
    args = parser.parse_args()

    manager = DeviceManager()
    manager.start()
    
    try:
        devs = find_devices(manager)
        if 'sidekick' not in devs or 'colorimeter' not in devs:
            print("Missing devices."); return

        sk = devs['sidekick']
        cm = devs['colorimeter']
        manager.connect_device(sk, 0, 0)
        manager.connect_device(cm, 0, 0)
        time.sleep(2)

        # 1. Home first to establish coordinate system
        print(f"\n{C.INFO}Homing...{C.END}")
        send_and_wait(manager, sk, {"func": "home"}, timeout=20)

        current_best_m1 = args.m1
        current_best_m2 = args.m2

        # 2. Move to initial Start
        print(f"\n{C.INFO}Moving to Start ({current_best_m1}, {current_best_m2})...{C.END}")
        move_to_absolute_steps(manager, sk, current_best_m1, current_best_m2)

        # 3. Scan M1 (keeping M2 fixed at initial)
        m1_data = scan_joint(manager, sk, cm, 'm1', current_best_m1, current_best_m2, args.range, args.step)
        best_m1, _ = find_valley_center(m1_data)
        current_best_m1 = best_m1 # Update our best guess for M1

        # 4. Move to center of M1 valley
        print(f"Centering M1 on {current_best_m1}...")
        move_to_absolute_steps(manager, sk, current_best_m1, current_best_m2)

        # 5. Scan M2 (keeping M1 fixed at new best)
        m2_data = scan_joint(manager, sk, cm, 'm2', current_best_m1, current_best_m2, args.range, args.step)
        _, best_m2 = find_valley_center(m2_data)
        current_best_m2 = best_m2 # Update our best guess for M2

        # 6. Final Result
        print(f"\n{C.OK}Final Center Found: ({current_best_m1}, {current_best_m2}){C.END}")
        
        # Save results
        final_output = {
            "initial_guess": {"m1": args.m1, "m2": args.m2},
            "parameters": {"range_steps": args.range, "step_size": args.step},
            "final_result": {"m1": current_best_m1, "m2": current_best_m2},
            "scan_data": {
                "m1_scan": m1_data,
                "m2_scan": m2_data
            }
        }

        with open(args.output, 'w') as f:
            json.dump(final_output, f, indent=2)
        print(f"Data saved to {args.output}")

    except KeyboardInterrupt:
        print("Aborted.")
    finally:
        manager.stop()

if __name__ == "__main__":
    main()