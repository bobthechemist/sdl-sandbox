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
from host.ai.ai_utils import (
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
            
            plan_steps = planner.create_plan(user_input)
            if not plan_steps:
                print(f"{C.WARN}Could not generate a plan. Please try again.{C.END}")
                continue

            # --- MODIFIED: Create the full output object ---
            output_data = {
                "user_prompt": user_input,
                "plan": plan_steps
            }

            print(f"\n{C.OK}--- Generated Plan ---{C.END}")
            print(json.dumps(output_data, indent=2))
            print(f"{C.OK}----------------------{C.END}")

            # --- Save the Plan ---
            output_file = args.output if args.output else f"{model['experiment_name']}_plan.json"
            save = input(f"\nSave this plan as '{output_file}'? [Y/n]: ").strip().lower()
            if save in ('', 'y', 'yes'):
                try:
                    with open(output_file, 'w') as f:
                        # Save the new output_data object, not just the plan_steps
                        json.dump(output_data, f, indent=2)
                    print(f"{C.OK}Plan saved. You can now run the executor:{C.END}")
                    world_file_arg = f"--world {args.world}" if args.world else f"--world {model['experiment_name']}_world.json"
                    print(f"  python host/ai/ai-execute.py --plan {output_file} {world_file_arg}")
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