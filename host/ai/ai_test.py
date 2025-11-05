import sys
import time
import queue
import re
import json
import argparse
from pathlib import Path

# Adjust the path to go up two directories from host/ai to the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from host.core.device_manager import DeviceManager
from host.core.discovery import find_data_comports
from host.firmware_db import get_device_name
from host.gui.console import C
from shared_lib.messages import Message
# NEW: Import the PlateManager
from host.lab.sidekick_plate_manager import PlateManager

# --- NEW: Planner Class ---

class Planner:
    """
    Analyzes a user's high-level goal and, using the world model and
    plate manager, generates a step-by-step plan of machine commands.
    """
    def __init__(self, world_model: dict, plate_manager: PlateManager, command_sets: dict):
        self.world_model = world_model
        self.plate_manager = plate_manager
        self.command_sets = command_sets
        # Invert the reagent map for easy lookup of pump from liquid name
        self.reagent_to_pump = {v: k for k, v in world_model.get('reagents', {}).items()}

    def create_plan(self, user_prompt: str):
        """
        Parses the user prompt and generates a plan.

        Returns:
            list: A list of command dictionaries representing the plan, or
            None: If a plan cannot be created.
        """
        prompt = user_prompt.lower()
        
        # --- Goal Identification ---
        # For now, we use a simple keyword-based approach.
        if "spectrum of" in prompt or "measure the spectrum" in prompt:
            # --- Entity Extraction ---
            # Find the name of the liquid the user mentioned.
            reagent_name = self._find_reagent_in_prompt(prompt)
            if not reagent_name:
                print(f"{C.ERR}[Planner] I couldn't identify a valid reagent in your request.{C.END}")
                return None
            
            # Generate the specific plan for this task
            return self._plan_measure_spectrum(reagent_name)
        
        else:
            print(f"{C.ERR}[Planner] I don't understand that request. I can only 'measure the spectrum of' a liquid for now.{C.END}")
            return None

    def _find_reagent_in_prompt(self, prompt: str) -> str | None:
        """Finds which of the known reagents is mentioned in the prompt."""
        for pump, reagent in self.world_model.get('reagents', {}).items():
            if reagent.lower() in prompt:
                return reagent
        return None

    def _plan_measure_spectrum(self, reagent_name: str):
        """Generates the specific command sequence for a single spectrum measurement."""
        print(f"{C.INFO}[Planner] Generating plan to measure spectrum for '{reagent_name}'...{C.END}")
        plan = []

        # 1. Validate Reagent and Get Pump ID
        pump_id = self.reagent_to_pump.get(reagent_name)
        if not pump_id:
            print(f"{C.ERR}[Planner] Error: Reagent '{reagent_name}' is not assigned to a pump.{C.END}")
            return None

        # 2. Select a Target Well
        target_well = self.plate_manager.find_empty_well()
        if not target_well:
            print(f"{C.ERR}[Planner] Error: Cannot create plan, the well plate is full.{C.END}")
            return None
        print(f"  -> Selecting empty well: {target_well}")

        # 3. Check Capacity and Volume
        dispense_vol = self.world_model['standard_dispense_ul']
        if not self.plate_manager.has_capacity_for(target_well, dispense_vol):
            print(f"{C.ERR}[Planner] Error: Well {target_well} does not have capacity for {dispense_vol}µL.{C.END}")
            return None
        
        # 4. Assemble the Plan
        print("  -> Assembling command sequence...")
        
        # Step A: Home the sidekick (always a good safety measure)
        plan.append({
            'device': 'sidekick',
            'command': 'home',
            'args': {}
        })

        # Step B: Move to the empty well
        plan.append({
            'device': 'sidekick',
            'command': 'to_well',
            'args': {'well': target_well}
        })
        
        # Step C: Dispense the liquid
        plan.append({
            'device': 'sidekick',
            'command': 'dispense',
            'args': {'pump': pump_id, 'vol': dispense_vol}
        })

        # Step D: Take the measurement
        plan.append({
            'device': 'colorimeter',
            'command': 'measure', # Using the sequencer-based command
            'args': {}
        })

        print(f"{C.OK}[Planner] Plan generated successfully with {len(plan)} steps.{C.END}")
        return plan

def world_building():
    # ... (function is unchanged)
    world_model = {}
    
    print("\n" + "="*60)
    print(" " * 16 + f"{C.INFO}AI Host: World Model Setup{C.END}" + " " * 17)
    print("="*60)
    print("Please answer the following questions to set up the experiment.")

    # --- 1. Reagent Mapping ---
    print(f"\n{C.WARN}[1] Reagent Configuration{C.END}")
    reagent_map = {}
    for i in range(1, 5):
        pump_id = f"p{i}"
        reagent_name = input(f"  -> What liquid is in pump {pump_id}? (Press Enter to skip): ").strip()
        if reagent_name:
            reagent_map[pump_id] = reagent_name
    world_model['reagents'] = reagent_map
    print(f"{C.OK}  Reagents mapped: {world_model['reagents']}{C.END}")

    # --- 2. Well Plate State ---
    print(f"\n{C.WARN}[2] Well Plate State{C.END}")
    while True:
        resp = input("  -> Can I assume the 96-well plate is completely empty? [y/n]: ").strip().lower()
        if resp in ('y', 'yes'):
            world_model['plate_is_empty'] = True
            break
        elif resp in ('n', 'no'):
            print(f"{C.ERR}  This script currently only supports starting with an empty plate. Aborting.{C.END}")
            return None # Abort the setup
        else:
            print(f"{C.ERR}  Invalid response. Please enter 'y' or 'n'.{C.END}")

    # --- 3. Maximum Well Volume ---
    print(f"\n{C.WARN}[3] Well Plate Parameters{C.END}")
    while True:
        try:
            max_vol = float(input("  -> What is the maximum safe volume for a single well (in µL)?: ").strip())
            if max_vol > 0:
                world_model['max_well_volume_ul'] = max_vol
                break
            else:
                print(f"{C.ERR}  Volume must be a positive number.{C.END}")
        except ValueError:
            print(f"{C.ERR}  Invalid input. Please enter a number.{C.END}")

    # --- 4. Standard Dispense Volume ---
    while True:
        try:
            std_vol = float(input(f"  -> What is the standard volume to dispense for tasks (in µL)?: ").strip())
            if std_vol <= 0:
                print(f"{C.ERR}  Volume must be a positive number.{C.END}")
            elif std_vol > world_model['max_well_volume_ul']:
                print(f"{C.ERR}  Standard volume cannot exceed the maximum volume ({world_model['max_well_volume_ul']} µL).{C.END}")
            else:
                world_model['standard_dispense_ul'] = std_vol
                break
        except ValueError:
            print(f"{C.ERR}  Invalid input. Please enter a number.{C.END}")
            
    # --- 7. Experiment Name ---
    print(f"\n{C.WARN}[4] Data Logging{C.END}")
    while True:
        exp_name = input("  -> What is the name for this experiment (for the output file)?: ").strip()
        sanitized_name = re.sub(r'[^\w\-_.]', '_', exp_name)
        if sanitized_name:
            world_model['experiment_name'] = sanitized_name
            print(f"{C.OK}  Data will be saved to '{sanitized_name}.csv'{C.END}")
            break
        else:
            print(f"{C.ERR}  Experiment name cannot be empty.{C.END}")

    # --- 8. Waste Location ---
    print(f"\n{C.WARN}[5] Waste Location{C.END}")
    waste_loc = input("  -> Where is the waste location? (e.g., 'A12' or '15.5, 2.0'): ").strip()
    world_model['waste_location'] = waste_loc

    # --- NEW: Save World Model ---
    while True:
        save_resp = input(f"\n{C.WARN}Would you like to save this world configuration for future use? [y/n]: {C.END}").strip().lower()
        if save_resp in ('y', 'yes'):
            filename = f"{world_model['experiment_name']}_world.json"
            try:
                with open(filename, 'w') as f:
                    json.dump(world_model, f, indent=4)
                print(f"{C.OK}  -> World model saved successfully to '{filename}'.{C.END}")
                print(f"{C.INFO}     You can reload this configuration later using:{C.END}")
                print(f"{C.INFO}     python ai-test.py --world {filename}{C.END}")
            except Exception as e:
                print(f"{C.ERR}  -> Error saving file: {e}{C.END}")
            break
        elif save_resp in ('n', 'no'):
            break
        else:
            print(f"{C.ERR}  Invalid response. Please enter 'y' or 'n'.{C.END}")

    print("\n" + "="*60)
    print(f"{C.OK}World model setup complete! The AI will operate with this configuration.{C.END}")
    print("="*60)
    
    return world_model

def load_world_from_file(filepath: str):
    # ... (function is unchanged)
    print(f"\n{C.INFO}[+] Loading world model from '{filepath}'...{C.END}")
    try:
        with open(filepath, 'r') as f:
            world_model = json.load(f)
        print(f"{C.OK}  -> World model loaded successfully.{C.END}")
        print("\n" + "="*60)
        print(f"{C.OK}The AI will operate with this loaded configuration.{C.END}")
        print("="*60)
        return world_model
    except FileNotFoundError:
        print(f"{C.ERR}  -> Error: The file was not found.{C.END}")
        return None
    except json.JSONDecodeError:
        print(f"{C.ERR}  -> Error: The file contains invalid JSON.{C.END}")
        return None
    except Exception as e:
        print(f"{C.ERR}  -> An unexpected error occurred while loading the file: {e}{C.END}")
        return None

def check_devices_attached():
    # ... (function is unchanged)
    print(f"{C.INFO}[+] Scanning for required devices (Sidekick and Colorimeter)...{C.END}")
    connected_ports = find_data_comports()

    if not connected_ports:
        print(f"{C.ERR}  -> No CircuitPython devices found.{C.END}")
        return False

    sidekick_found = False
    colorimeter_found = False

    print("  -> Found the following devices:")
    for port_info in connected_ports:
        friendly_name = get_device_name(port_info['VID'], port_info['PID'])
        print(f"     - {friendly_name} on {port_info['port']}")
        
        if 'sidekick' in friendly_name.lower(): sidekick_found = True
        if 'colorimeter' in friendly_name.lower(): colorimeter_found = True

    if sidekick_found and colorimeter_found:
        print(f"{C.OK}\n[SUCCESS] Both Sidekick and Colorimeter are attached.{C.END}")
        return True
    else:
        print(f"{C.ERR}\n[FAILURE] One or more required devices were not found.{C.END}")
        if not sidekick_found: print(f"{C.ERR}  - Sidekick is missing.{C.END}")
        if not colorimeter_found: print(f"{C.ERR}  - Colorimeter is missing.{C.END}")
        return False

def connect_devices():
    # ... (function is unchanged)
    print(f"\n{C.INFO}[+] Initializing Device Manager and connecting to devices...{C.END}")
    manager = DeviceManager()
    manager.start()

    device_ports_map = {}
    all_ports = find_data_comports()

    for port_info in all_ports:
        port, vid, pid = port_info['port'], port_info['VID'], port_info['PID']
        friendly_name = get_device_name(vid, pid)
        device_key = None
        if 'sidekick' in friendly_name.lower(): device_key = 'sidekick'
        elif 'colorimeter' in friendly_name.lower(): device_key = 'colorimeter'
        
        if device_key:
            print(f"  -> Attempting to connect to {friendly_name} on {port}...")
            if manager.connect_device(port, vid, pid):
                device_ports_map[device_key] = port
                print(f"{C.OK}     Connection successful.{C.END}")
            else:
                print(f"{C.ERR}     Connection failed.{C.END}")
                manager.stop()
                return None, None
    
    return manager, device_ports_map

def get_instructions(manager: DeviceManager, device_ports: dict, timeout: int = 5):
    # ... (function is unchanged)
    print(f"\n{C.INFO}[+] Retrieving command lists from all devices...{C.END}")
    help_payload = {"func": "help", "args": {}}
    help_message = Message.create_message("AI_HOST", "INSTRUCTION", payload=help_payload)
    
    for device, port in device_ports.items():
        print(f"  -> Sending 'help' to {device} on {port}")
        manager.send_message(port, help_message)

    all_commands = {}
    start_time = time.time()
    print("  -> Waiting for responses...")

    while len(all_commands) < len(device_ports) and time.time() - start_time < timeout:
        try:
            msg_type, port, msg_data = manager.incoming_message_queue.get_nowait()
            if msg_type == 'RECV' and msg_data.status == "DATA_RESPONSE":
                payload_data = msg_data.payload.get('data', {})
                if 'ping' in payload_data and 'description' in payload_data.get('ping', {}):
                    for name, p in device_ports.items():
                        if p == port and name not in all_commands:
                            print(f"{C.OK}     Received command list from {name}.{C.END}")
                            all_commands[name] = payload_data
                            break
        except queue.Empty:
            time.sleep(0.1)

    if len(all_commands) < len(device_ports):
        print(f"{C.ERR}[FAILURE] Timed out waiting for all devices to respond.{C.END}")
        return None
        
    return all_commands

def print_command_summary(all_commands: dict):
    # ... (function is unchanged)
    print("\n" + "="*80)
    print(" " * 28 + "COMMAND SUMMARY FOR AI HOST")
    print("="*80)
    
    for device_name, commands in all_commands.items():
        print(f"\n--- {device_name.upper()} Commands ---")
        sorted_command_names = sorted(commands.keys())
        for command_name in sorted_command_names:
            details = commands[command_name]
            description = details.get('description', 'No description available.')
            print(f"  {C.OK}{command_name:<15}{C.END} | {description}")
    print("\n" + "="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Host for the Self-Driving Laboratory.")
    parser.add_argument('--world', type=str, help="Path to a JSON file containing a pre-configured world model.")
    args = parser.parse_args()

    print("====== AI Test Script ======")
    manager = None
    try:
        # --- Step 1: Establish the World Model ---
        model = None
        if args.world:
            model = load_world_from_file(args.world)
            if not model: sys.exit(1)
        else:
            model = world_building()

        if not model:
            print("\nSetup was aborted by the user.")
            sys.exit(0)
        
        # --- Step 2: Check devices and connect ---
        if not check_devices_attached(): sys.exit(1)
        manager, device_ports = connect_devices()
        if not manager or not device_ports:
            print(f"{C.ERR}Could not establish connections. Aborting.{C.END}")
            sys.exit(1)
        
        time.sleep(2)
        
        # --- Step 3: Get command sets ---
        command_sets = get_instructions(manager, device_ports)
        if not command_sets:
             raise RuntimeError("Failed to retrieve commands from devices.")

        print_command_summary(command_sets)
        
        # --- NEW: Instantiate Managers and Planner ---
        plate_manager = PlateManager(max_volume_ul=model['max_well_volume_ul'])
        planner = Planner(world_model=model, plate_manager=plate_manager, command_sets=command_sets)
        
        # --- Step 4: Main AI Operational Loop ---
        print("\n" + "="*60)
        print(f" " * 18 + f"{C.INFO}AI Operational Loop Initialized{C.END}" + " " * 17)
        print("="*60)

        while True:
            user_input = input(f"\n{C.WARN}What would you like me to do? (type 'quit' to exit): {C.END}").strip()
            
            if user_input.lower() == 'quit':
                break
            
            # Generate a plan based on the user's request
            plan = planner.create_plan(user_input)

            if plan:
                print(f"\n{C.OK}Generated Plan:{C.END}")
                # Pretty-print the plan for review
                print(json.dumps(plan, indent=4))
                # TODO: Execute the plan
            else:
                print(f"{C.WARN}Could not generate a plan for that request. Please try again.{C.END}")
        
    except Exception as e:
        print(f"\n{C.ERR}An unexpected error occurred in the main script: {e}{C.END}")
    finally:
        if manager:
            print(f"\n{C.INFO}Shutting down Device Manager...{C.END}")
            manager.stop()
            print("Shutdown complete.")
    print("============================")