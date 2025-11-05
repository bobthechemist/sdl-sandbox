# host/ai/planner.py
import re
import json
from host.lab.sidekick_plate_manager import PlateManager
from host.ai.vertext_agent import Agent
from host.gui.console import C

class Planner:
    """
    Uses a Large Language Model to analyze a user's goal and generate a
    step-by-step plan of machine commands.
    """
    def __init__(self, world_model: dict, plate_manager: PlateManager, command_sets: dict):
        self.world_model = world_model
        self.plate_manager = plate_manager
        self.command_sets = command_sets
        
        base_context = (
            "You are an expert laboratory automation planner. Your task is to convert a user's "
            "high-level request into a precise, machine-executable plan in JSON format. "
            "Analyze the available commands, the current world configuration, and the real-time state "
            "of the well plate to generate a valid and logical sequence of actions. "
            "You MUST ONLY respond with the JSON plan and nothing else."
        )
        self.agent = Agent(context=base_context)

    def _build_llm_prompt(self, user_prompt: str) -> str:
        """Constructs the full, context-rich prompt to send to the LLM."""
        
        empty_wells = [
            well for well, state in self.plate_manager.plate_state.items() 
            if self.plate_manager.is_well_empty(well) and well != 'waste'
        ]

        # --- MODIFICATION: The prompt is now much more explicit ---
        prompt = f"""
Here is the complete context for the task.

# 1. COMMANDS AVAILABLE
The following commands are available to you, grouped by device:
{json.dumps(self.command_sets, indent=2)}

# 2. WORLD CONFIGURATION
This is the user-defined setup for the current experiment:
{json.dumps(self.world_model, indent=2)}

# 3. CURRENT PLATE STATE
This is the real-time status of the 96-well plate.
- empty_wells: {json.dumps(empty_wells[:12])} ... (showing first 12)

# 4. WORKFLOW DEFINITIONS  <-- NEW, CRITICAL SECTION
- To "measure the spectrum of a liquid", you MUST follow this sequence:
  1. Select an empty well from the 'empty_wells' list.
  2. Use the 'sidekick' to 'dispense' the correct liquid into that chosen well.
  3. Use the 'colorimeter' to perform the measurement on that same well. The 'measure' command is preferred as it is a complete action.

# 5. RULES
- Always start a new sequence of movements with a 'sidekick' 'home' command.
- When dispensing a liquid, use the 'standard_dispense_ul' from the WORLD CONFIGURATION unless the user specifies a different volume.
- When a well is needed and not specified by the user, you MUST select one from the 'empty_wells' list.
- Before planning a dispense action, you MUST verify the target well has capacity.
- **Prefer using high-level, multi-step commands like `colorimeter.measure` over low-level ones like `read_all` and `set_settings`.** <-- NEW RULE

# 6. JSON OUTPUT FORMAT
Your output MUST be a JSON array of objects. Each object represents one step in the plan.
Example of a valid response:
[
  {{
    "device": "sidekick",
    "command": "home",
    "args": {{}}
  }},
  {{
    "device": "sidekick",
    "command": "dispense_at",
    "args": {{"well": "A1", "pump": "p1", "vol": 150}}
  }}
]

# 7. USER REQUEST
Based on all the information and workflow definitions above, generate a complete JSON plan for the following user request:
"{user_prompt}"
"""
        return prompt

    def create_plan(self, user_prompt: str):
        # ... (This method remains unchanged)
        if not self.world_model.get('reagents'):
            print(f"{C.ERR}[Planner] Cannot create a plan. No reagents have been defined in the world model.{C.END}")
            return None

        full_prompt = self._build_llm_prompt(user_prompt)
        
        print(f"\n{C.INFO}[Planner] Contacting AI model to generate a plan... please wait.{C.END}")
        response_text = self.agent.prompt(full_prompt, use_history=False)

        if not response_text:
            print(f"{C.ERR}[Planner] Received no response from the AI model.{C.END}")
            return None

        try:
            json_match = re.search(r'```(json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(2)
            else:
                json_str = response_text

            plan = json.loads(json_str)
            
            if isinstance(plan, list) and all('device' in step and 'command' in step for step in plan):
                 print(f"{C.OK}[Planner] Plan generated and validated successfully.{C.END}")
                 return plan
            else:
                raise ValueError("Parsed JSON is not in the correct format (list of steps).")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"{C.ERR}[Planner] Failed to parse a valid plan from the AI's response.{C.END}")
            print(f"  -> Error: {e}")
            print(f"  -> Raw AI Response:\n{response_text}")
            return None