#!/usr/bin/env python3
"""
Talos-SDL Socratic Instrument Designer
A tool to guide hardware developers through state-machine and command-interface 
design using interactive, reflective prompts.
"""

import sys
import os
import json

class C:
    OK = '\033[92m'
    WARN = '\033[93m'
    ERR = '\033[91m'
    INFO = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print(f"\n{C.BOLD}{C.INFO}=== {title} ==={C.END}\n")

def socratic_prompt(question, tip, placeholder=None):
    """Prints a Socratic thinking tip before asking the question."""
    print(f"{C.BOLD}Thinking Tip:{C.END} {C.WARN}{tip}{C.END}")
    if placeholder:
        print(f"{C.INFO}Example:{C.END} {placeholder}")
    ans = input(f"{C.BOLD}> {question}:{C.END}\n").strip()
    while not ans:
        print(f"{C.ERR}This field is required to build a valid design specification.{C.END}")
        ans = input(f"{C.BOLD}> {question}:{C.END}\n").strip()
    print("-" * 60)
    return ans

def yes_no_prompt(question, tip):
    print(f"{C.BOLD}Thinking Tip:{C.END} {C.WARN}{tip}{C.END}")
    while True:
        ans = input(f"{C.BOLD}> {question} (y/n):{C.END}\n").strip().lower()
        if ans in ('y', 'yes'):
            print("-" * 60)
            return True
        elif ans in ('n', 'no'):
            print("-" * 60)
            return False
        print(f"{C.ERR}Please enter 'y' or 'n'.{C.END}")

def main():
    clear_screen()
    print(f"{C.OK}{C.BOLD}====================================================")
    print("      Talos-SDL Socratic Instrument Designer        ")
    print(f"===================================================={C.END}")
    print("This assistant will guide you through the architectural design of")
    print("your new instrument's firmware. We will construct a formal design")
    print("specification to ensure physical safety, non-blocking state updates,")
    print("and clean command abstraction before generating any code.")
    
    # ==========================================
    # PHASE 1: HIGH-LEVEL DEFINITION
    # ==========================================
    print_header("Phase 1: High-Level Instrument Definition")
    
    subsystem_name = socratic_prompt(
        "Enter a unique name/ID for this subsystem (UPPERCASE_SNAKE_CASE)",
        "Use a clear, concise name that represents the hardware domain.",
        "e.g., SYRINGE_PUMP, HEATER_BLOCK, LIQUID_SENSOR"
    ).upper()

    purpose = socratic_prompt(
        "What is the single, primary responsibility of this instrument?",
        "Socratic Check: If your instrument does more than one distinct task, "
        "could it be split into separate virtual devices to lower architectural complexity?",
        "e.g., 'To precisely heat a vial and maintain temperature,' or 'To draw and dispense liquid volumes.'"
    )

    actions = socratic_prompt(
        "List the primary hardware actions this device must perform",
        "Keep this at a high level. We will detail states and commands later.",
        "e.g., 'Homings motors, toggling a relay, measuring voltage averages.'"
    )

    telemetry = socratic_prompt(
        "What physical values must this instrument stream back periodically?",
        "Socratic Check: Telemetry should only include properties that change dynamically "
        "and are valuable to log. Static configuration belongs elsewhere.",
        "e.g., 'Internal temperature in Celsius, current optical density value, pressure in PSI.'"
    )

    failures = socratic_prompt(
        "What are the critical failure modes of this hardware?",
        "Socratic Check: Consider both electrical faults (unresponsive I2C) and mechanical safety "
        "(limit switch triggered, overheating threshold exceeded).",
        "e.g., 'Thermistor disconnects, motor stalls during homing, limit switch fails to toggle.'"
    )

    guidance = socratic_prompt(
        "What operational guidance does an AI agent need to interact with this device?",
        "Socratic Check: If this device is physically co-located with others, are there "
        "ordering constraints? (e.g., does a robotic arm need to place a vial here first?)",
        "e.g., 'This device must be homed before any dispense commands can run. A robotic arm "
        "must place a microwell plate on the stage before launching a scan command.'"
    )

    # ==========================================
    # PHASE 2: HARDWARE CONFIGURATION (SUBSYSTEM_CONFIG)
    # ==========================================
    print_header("Phase 2: Hardware Configuration (SUBSYSTEM_CONFIG)")
    print("Now we define static properties: microchip pins, defaults, and physical guard rails.")
    
    pins = {}
    print(f"\n{C.BOLD}--- Step 2A: Pin Mapping ---{C.END}")
    if yes_no_prompt("Do you need to map specific GPIO pins for this instrument?", 
                     "Simple I2C sensors often use defaults, but motors, heaters, and analog detectors need direct pin definitions."):
        while True:
            pin_name = input(f"{C.BOLD}Pin identifier name (e.g., STEP_PIN, RELAY_PIN, sensor_rx): {C.END}").strip()
            if not pin_name:
                break
            pin_val = input(f"{C.BOLD}Microcontroller pin object (e.g., board.D12, board.GP5): {C.END}").strip()
            pins[pin_name] = pin_val
            if not yes_no_prompt("Add another pin?", "Consider all inputs, outputs, and interface lines."):
                break

    parameters = {}
    print(f"\n{C.BOLD}--- Step 2B: Operational Parameters & Settings ---{C.END}")
    if yes_no_prompt("Does your hardware have configurable operational parameters?", 
                     "These are parameters such as default speeds, microstepping variables, or amplification gains."):
        while True:
            param_name = input(f"{C.BOLD}Parameter Name (e.g., default_speed, sensor_gain): {C.END}").strip()
            if not param_name:
                break
            param_val = input(f"{C.BOLD}Default Value (e.g., 500, 64, 0.05): {C.END}").strip()
            parameters[param_name] = param_val
            if not yes_no_prompt("Add another operational parameter?", "Think about defaults that avoid hardcoding values inside your execution logic."):
                break

    limits = {}
    print(f"\n{C.BOLD}--- Step 2C: Physical Safety Limits ---{C.END}")
    if yes_no_prompt("Does this device have safety boundaries?", 
                     "Socratic Check: What physical inputs or values would cause permanent hardware damage if exceeded?"):
        while True:
            limit_name = input(f"{C.BOLD}Limit name (e.g., max_temperature_c, max_steps): {C.END}").strip()
            if not limit_name:
                break
            limit_val = input(f"{C.BOLD}Value limit (e.g., 85, 20000): {C.END}").strip()
            limits[limit_name] = limit_val
            if not yes_no_prompt("Add another physical safety limit?", "Ensure you have defined boundaries for every physical variable."):
                break

    # ==========================================
    # PHASE 3: COMMAND INTERFACE
    # ==========================================
    print_header("Phase 3: Command Interface (The API)")
    print("Here we define how the host application or AI agents will control this hardware.")
    
    commands = []
    while True:
        cmd_name = input(f"\n{C.BOLD}Command Function Name (lowercase, e.g., dispense, heat_vial): {C.END}").strip()
        if not cmd_name:
            if not commands:
                print(f"{C.ERR}You must specify at least one custom command for your API.{C.END}")
                continue
            break
            
        print(f"\nDefining command: {C.BOLD}{cmd_name}{C.END}")
        desc = socratic_prompt(
            "What does this command do?",
            "Keep the description highly descriptive. AI planners rely on these strings to select commands.",
            "e.g., 'Dispenses a specified volume of liquid from a target pump channel.'"
        )
        
        ai_enabled = yes_no_prompt(
            "Should this command be exposed to autonomous AI agents?",
            "Socratic Check: High-level abstract goals (e.g., 'dispense') should be AI-enabled. "
            "Low-level commands that can cause damage if run out of sequence (e.g., raw 'step') should be restricted."
        )

        args = []
        if yes_no_prompt("Does this command require arguments?", "If the host must provide values (like speeds, targets, or volumes) to execute this command."):
            while True:
                arg_name = input(f"{C.BOLD}  Argument Name (e.g., vol, target_temp, pump_id): {C.END}").strip()
                if not arg_name:
                    break
                arg_type = input(f"{C.BOLD}  Argument Type (e.g., float, int, str): {C.END}").strip()
                arg_def = input(f"{C.BOLD}  Default Value (leave empty if mandatory): {C.END}").strip()
                
                arg_dict = {"name": arg_name, "type": arg_type}
                if arg_def:
                    arg_dict["default"] = arg_def
                args.append(arg_dict)
                if not yes_no_prompt("  Add another argument for this command?", "Ensure you have defined all variables needed for this action."):
                    break

        success = socratic_prompt(
            "What constitutes successful execution of this command?",
            "What response does the host expect? (e.g., Success confirmation, transition to another state, or specific data).",
            "e.g., 'Returns a SUCCESS payload upon completion of step limits,' or 'Transitions to State: Heating.'"
        )

        guards = socratic_prompt(
            "What criteria must be met BEFORE accepting this command?",
            "Socratic Check: How can we prevent execution if the hardware state is unsafe? (e.g., block dispensing if not homed).",
            "e.g., 'Must be in IDLE state. Target volume cannot exceed remaining capacity.'"
        )

        commands.append({
            "func": cmd_name,
            "description": desc,
            "ai_enabled": ai_enabled,
            "args": args,
            "success": success,
            "guards": guards
        })

        if not yes_no_prompt("Add another command to your API?", "Think about standard calibration, actions, or measurements."):
            break

    # ==========================================
    # PHASE 4: STATE MACHINE STATES
    # ==========================================
    print_header("Phase 4: Defining State Machine States")
    print("Talos-SDL implements: StateMachine.update() running non-blocking operations on a fast loop.")
    print(f"By default, your device inherits {C.OK}GenericIdle{C.END} and {C.OK}GenericError{C.END}.")
    print("You only need to design custom operational or transitional states.")

    custom_states = []
    while True:
        state_name = input(f"\n{C.BOLD}Custom State Name (PascalCase, e.g., Homing, Dispensing, ReadSensor): {C.END}").strip()
        if not state_name:
            if not custom_states:
                print(f"{C.ERR}You must specify at least one state (typically an initialization or active routine state).{C.END}")
                continue
            break

        print(f"\nDesigning state: {C.BOLD}{state_name}{C.END}")
        purpose = socratic_prompt(
            "What is this state's single, clear responsibility?",
            "Each state should focus on one logical operation.",
            "e.g., 'Actively running motor step sequences until a target position or physical limit is reached.'"
        )

        entry = socratic_prompt(
            "What actions occur immediately when ENTERING this state?",
            "Initialize timers, turn on pins, or reset coordinate counts here.",
            "e.g., 'Sets the start timestamp, turns on the heater relay pin, and resets the target reached flag.'"
        )

        internal = socratic_prompt(
            "What calculations or actions occur on every UPDATE loop?",
            "Socratic Check: This runs hundreds of times per second. It MUST be non-blocking. "
            "Never use sleep statements or long loops here. Check conditions and return immediately.",
            "e.g., 'Reads current sensor voltage, checks if current time exceeds safety timeout.'"
        )

        exit_triggers = socratic_prompt(
            "What triggers transition out of this state, and where do we go next?",
            "Socratic Check: What paths exist? (Success paths vs. Failure/Error paths).",
            "e.g., 'Success: sensor reaches target temperature (transitions to Idle). Failure: timeout exceeded (transitions to Error).'"
        )

        exit_actions = socratic_prompt(
            "What cleanup occurs when EXITING this state?",
            "Ensure the hardware is left in a safe electrical and mechanical state.",
            "e.g., 'Disables the heater relay pin to ensure heating stops immediately upon state departure.'"
        )

        custom_states.append({
            "name": state_name,
            "purpose": purpose,
            "entry": entry,
            "internal": internal,
            "exit_triggers": exit_triggers,
            "exit_actions": exit_actions
        })

        if not yes_no_prompt("Add another custom state?", "Consider setup, steady-states, or shutdown routines."):
            break

    # ==========================================
    # WRITE DESIGN SPECIFICATION TO MARKDOWN
    # ==========================================
    output_filename = "talos_design_spec.md"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(f"# Talos-SDL Instrument Design Specification: {subsystem_name}\n\n")
        f.write("This document was generated interactively using the Socratic method.\n\n")
        
        f.write("## 1. High-Level Definition\n")
        f.write(f"*   **Primary Purpose:** {purpose}\n")
        f.write(f"*   **Primary Actions:** {actions}\n")
        f.write(f"*   **Telemetry Outputs:** {telemetry}\n")
        f.write(f"*   **Failure Conditions:** {failures}\n")
        f.write(f"*   **AI Agent Operational Guidance:** {guidance}\n\n")
        
        f.write("## 2. Hardware Configuration (`SUBSYSTEM_CONFIG`)\n")
        f.write("### GPIO Pin Mapping\n")
        if pins:
            f.write("| Pin Identifier | Physical Pin Object |\n")
            f.write("| :--- | :--- |\n")
            for p_name, p_val in pins.items():
                f.write(f"| {p_name} | {p_val} |\n")
        else:
            f.write("No custom pins defined (uses standard serial or defaults).\n")
        f.write("\n")
        
        f.write("### Operational Parameters & Settings\n")
        if parameters:
            f.write("| Parameter Name | Default Value |\n")
            f.write("| :--- | :--- |\n")
            for p_name, p_val in parameters.items():
                f.write(f"| {p_name} | {p_val} |\n")
        else:
            f.write("No custom parameters defined.\n")
        f.write("\n")
        
        f.write("### Safety & Guard Limits\n")
        if limits:
            f.write("| Boundary Name | Value Limit |\n")
            f.write("| :--- | :--- |\n")
            for l_name, l_val in limits.items():
                f.write(f"| {l_name} | {l_val} |\n")
        else:
            f.write("No safety limits specified.\n")
        f.write("\n")
        
        f.write("## 3. Command Interface (The API)\n")
        for cmd in commands:
            f.write(f"### Command: `{cmd['func']}`\n")
            f.write(f"*   **Description:** {cmd['description']}\n")
            f.write(f"*   **AI Agent Accessible:** `{cmd['ai_enabled']}`\n")
            f.write(f"*   **Success Metric:** {cmd['success']}\n")
            f.write(f"*   **Command Guards:** {cmd['guards']}\n")
            f.write("*   **Arguments:**\n")
            if cmd['args']:
                for arg in cmd['args']:
                    def_str = f" (Default: {arg['default']})" if "default" in arg else " (Required)"
                    f.write(f"    *   `{arg['name']}` ({arg['type']}){def_str}\n")
            else:
                f.write("    *   None\n")
            f.write("\n")
            
        f.write("## 4. State Machine Custom States\n")
        for st in custom_states:
            f.write(f"### State: `{st['name']}`\n")
            f.write(f"*   **Single Responsibility:** {st['purpose']}\n")
            f.write(f"*   **Entry Actions (`enter()`):** {st['entry']}\n")
            f.write(f"*   **Internal Operations (`update()`):** {st['internal']}\n")
            f.write(f"*   **Transition & Exit Events:** {st['exit_triggers']}\n")
            f.write(f"*   **Exit Cleanup Actions (`exit()`):** {st['exit_actions']}\n\n")
            
    print(f"\n{C.OK}{C.BOLD}Success! Design Spec Sheet compiled and saved to: {output_filename}{C.END}")
    print("\nHow to proceed to code generation (Part 2):")
    print(f"1. Open '{output_filename}' to confirm your responses are structured cleanly.")
    print("2. Feed this Markdown spec sheet directly into your AI assistant, junto with")
    print("   the system prompt template (`developer_guides/ai_agent_prompt_templates/firmware_generation_template.md`).")
    print("3. The generated code will match your designed state machine exactly.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.ERR}Design process cancelled by user.{C.END}")
        sys.exit(0)