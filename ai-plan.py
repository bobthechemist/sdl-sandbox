# host/ai/ai-plan.py
import sys
import json
import argparse
from pathlib import Path

# Setup project root path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Local and project imports
from host.lab.sidekick_plate_manager import PlateManager
from host.ai.planner import Planner
from host.gui.console import C
# Import setup functions from the old script (assuming they are moved to a utils file or kept here)
from host.ai.ai_test import (
    world_building, load_world_from_file, check_devices_attached,
    connect_devices, get_instructions
)

def main():
    parser = argparse.ArgumentParser(description="Generate an experimental plan using the AI Planner.")
    parser.add_argument('--world', type=str, help="Path to a pre-configured world model JSON file.")
    parser.add_argument('--output', type=str, help="Optional: Filename for the output plan JSON file.")
    args = parser.parse_args()

    print("====== AI Experiment Planner ======")
    manager = None
    try:
        # --- Setup Phase ---
        model = load_world_from_file(args.world) if args.world else world_building()
        if not model:
            sys.exit("World model setup failed or was aborted.")

        if not check_devices_attached(): sys.exit(1)
        manager, device_ports = connect_devices()
        if not manager: sys.exit("Could not connect to devices.")
        
        command_sets = get_instructions(manager, device_ports)
        if not command_sets: sys.exit("Failed to retrieve commands.")

        plate_manager = PlateManager(max_volume_ul=model['max_well_volume_ul'])
        planner = Planner(world_model=model, plate_manager=plate_manager, command_sets=command_sets)
        
        # --- Planning Loop ---
        while True:
            user_input = input(f"\n{C.WARN}Enter your goal (or 'quit'): {C.END}").strip()
            if user_input.lower() == 'quit': break
            
            plan = planner.create_plan(user_input)
            if not plan:
                print(f"{C.WARN}Could not generate a plan. Please try again.{C.END}")
                continue

            print(f"\n{C.OK}--- Generated Plan ---{C.END}")
            print(json.dumps(plan, indent=2))
            print(f"{C.OK}----------------------{C.END}")

            # --- Save the Plan ---
            output_file = args.output if args.output else f"{model['experiment_name']}_plan.json"
            save = input(f"\nSave this plan as '{output_file}'? [Y/n]: ").strip().lower()
            if save in ('', 'y', 'yes'):
                try:
                    with open(output_file, 'w') as f:
                        json.dump(plan, f, indent=2)
                    print(f"{C.OK}Plan saved. You can now run the executor:{C.END}")
                    print(f"  python host/ai/ai-execute.py {output_file} --world {args.world or 'your_world_file.json'}")
                except Exception as e:
                    print(f"{C.ERR}Error saving plan: {e}{C.END}")

    except Exception as e:
        print(f"\n{C.ERR}An unexpected error occurred: {e}{C.END}")
    finally:
        if manager:
            print(f"\n{C.INFO}Shutting down Device Manager...{C.END}")
            manager.stop()

if __name__ == "__main__":
    main()