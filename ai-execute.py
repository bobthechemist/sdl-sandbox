# host/ai/ai-execute.py
import sys
import json
import time
import queue
import csv
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from host.core.device_manager import DeviceManager
from host.lab.sidekick_plate_manager import PlateManager
from host.gui.console import C
from shared_lib.messages import Message
from host.ai.ai_utils import connect_devices, load_world_from_file

def wait_for_completion(
    manager: DeviceManager,
    port: str,
    step_info: dict,
    csv_writer: csv.DictWriter,
    header_written: bool,
    timeout: int = 60
):
    """Waits for a completion message and logs any DATA_RESPONSE to the CSV."""
    # ... (This function remains unchanged as its logic is still correct)
    print(f"  -> Waiting for completion from {port} (timeout: {timeout}s)...")
    start_time = time.time()
    header_was_written = header_written

    while time.time() - start_time < timeout:
        try:
            msg_type, msg_port, msg_data = manager.incoming_message_queue.get(timeout=1)
            if msg_port != port:
                continue

            status = msg_data.status.upper()
            payload = msg_data.payload

            if status in ("SUCCESS", "DATA_RESPONSE"):
                print(f"{C.OK}  -> Received {status}{C.END}")
                
                if status == "DATA_RESPONSE":
                    data_points = payload.get('data', {})
                    if isinstance(data_points, dict):
                        log_row = {
                            'timestamp': datetime.now().isoformat(),
                            'step': step_info['number'],
                            'device': step_info['device'],
                            'command': step_info['command'],
                        }
                        log_row.update(data_points)
                        
                        if not header_was_written:
                            csv_writer.fieldnames = log_row.keys()
                            csv_writer.writeheader()
                            header_was_written = True
                        
                        csv_writer.writerow(log_row)
                        print(f"  -> {C.INFO}Logged data response to CSV.{C.END}")

                return True, payload, header_was_written

            elif status == "PROBLEM":
                print(f"{C.ERR}  -> Received PROBLEM: {payload}{C.END}")
                return False, payload, header_was_written

        except queue.Empty:
            continue

    print(f"{C.ERR}  -> Timed out waiting for response from {port}.{C.END}")
    return False, None, header_was_written


def main():
    parser = argparse.ArgumentParser(description="Execute a pre-generated experimental plan.")
    parser.add_argument("--plan", type=str, required=True, help="Path to the plan JSON file.")
    parser.add_argument("--world", type=str, required=True, help="Path to the world model JSON file for this plan.")
    parser.add_argument("--output", type=str, help="Optional: Name of the output CSV file for results.")
    args = parser.parse_args()

    print("====== AI Experiment Executor ======")
    manager = None
    output_csv_file = None
    try:
        # --- Setup Phase ---
        world_model = load_world_from_file(args.world)
        if not world_model: sys.exit(1)

        # --- MODIFIED: Robust plan loading ---
        try:
            with open(args.plan, 'r') as f:
                data = json.load(f)

            plan = []
            if isinstance(data, dict) and 'plan' in data:
                # New format: {"user_prompt": "...", "plan": [...]}
                plan = data['plan']
                user_prompt = data.get('user_prompt', 'Not found in plan file.')
                print(f"{C.INFO}Executing plan for prompt: '{user_prompt}'{C.END}")
            elif isinstance(data, list):
                # Old format: [...]
                plan = data
                print(f"{C.WARN}Warning: This is an old plan format without a user prompt.{C.END}")
            else:
                sys.exit(f"{C.ERR}Invalid plan file format. Expected a list of steps or an object with a 'plan' key.{C.END}")

            print(f"{C.OK}Loaded plan with {len(plan)} steps from '{args.plan}'.{C.END}")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            sys.exit(f"{C.ERR}Failed to load or parse plan file: {e}{C.END}")

        manager, device_ports = connect_devices()
        if not manager: sys.exit(1)
        
        plate_manager = PlateManager(max_volume_ul=world_model['max_well_volume_ul'])
        time.sleep(2)

        output_filename = args.output if args.output else f"{world_model.get('experiment_name', 'experiment')}_results.csv"
        print(f"{C.INFO}Results will be logged to '{output_filename}'{C.END}")
        output_csv_file = open(output_filename, 'w', newline='')
        csv_writer = csv.DictWriter(output_csv_file, fieldnames=[])
        header_written = False

        # --- Execution Loop ---
        print("\n" + "="*60)
        print(" " * 22 + "Starting Plan Execution")
        print("="*60 + "\n")

        for i, step in enumerate(plan):
            # ... (Rest of the execution loop is unchanged)
            step_num = i + 1
            print(f"{C.WARN}Step {step_num}/{len(plan)}: {step['device']} -> {step['command']}{C.END}")
            
            port = device_ports.get(step['device'])
            if not port:
                print(f"{C.ERR}  -> Aborting: Device '{step['device']}' is not connected.{C.END}")
                break
            
            msg = Message("AI_EXECUTOR", "INSTRUCTION", payload={"func": step['command'], "args": step['args']})
            manager.send_message(port, msg)
            
            step_info = {'number': step_num, 'device': step['device'], 'command': step['command']}
            success, response, header_written = wait_for_completion(manager, port, step_info, csv_writer, header_written)

            if not success:
                print(f"{C.ERR}  -> Aborting plan due to error in step {step_num}.{C.END}")
                break
            
            if step['command'] in ('dispense', 'dispense_at', 'to_well_and_dispense'):
                args = step['args']
                # Correctly handle getting well from different command structures
                well = args.get('well') if 'well' in args else args.get('to_well')
                pump = args.get('pump')
                vol = args.get('vol')
                if well and pump and vol:
                    plate_manager.add_liquid(well, pump, vol)
                    print(f"  -> {C.INFO}Updated PlateManager: Added {vol}µL from {pump} to {well}.{C.END}")

            time.sleep(1)

        print("\n" + "="*60)
        print(" " * 23 + "Plan Execution Finished")
        print("="*60)

    except Exception as e:
        print(f"\n{C.ERR}An unexpected error occurred: {e}{C.END}")
    finally:
        if manager:
            print(f"\n{C.INFO}Shutting down Device Manager...{C.END}")
            manager.stop()
        if output_csv_file:
            output_csv_file.close()
            print("Output file closed.")

if __name__ == "__main__":
    main()