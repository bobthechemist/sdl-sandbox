import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# --- Path Setup to include 'host' package ---
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from host.ai.llm_manager import LLMManager 
from dln import DigitalLabNotebook, verification # New DLN imports
from host.gui.console import C

# Load environment variables (API Keys)
load_dotenv()

def load_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"{C.ERR}Error: File not found '{filepath}'{C.END}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate a Lab Report from Digital Lab Notebook (DLN) records.")
    
    # Arguments
    parser.add_argument("experiment_id", type=int, help="The ID of the experiment session to summarize.")
    parser.add_argument("--output", required=True, help="Filename for the output Markdown report.")
    parser.add_argument("--template", required=True, help="Path to the Markdown template file.")
    parser.add_argument("--agent", default="gemini", help="AI Provider (default: gemini).")
    parser.add_argument("--model", default="gemini-flash-lite-latest", help="Model name (default: gemini-flash-lite-latest).")

    args = parser.parse_args()

    # Load Data from New DLN
    print(f"{C.INFO}Loading log data and template...{C.END}")
    template_content = load_file(args.template)

    # Initialize the new DLN (assuming it's in .talos)
    notebook = DigitalLabNotebook(db_path=".talos/lab_notebook.db") 
    
    # Retrieve ExperimentSession data
    exp_session_raw = notebook.query_relational(
        f"SELECT id, title, start_time, end_time, context_json, final_summary, final_hash, status "
        f"FROM ExperimentSession WHERE id = {args.experiment_id}"
    )
    if not exp_session_raw:
        print(f"{C.ERR}Error: Experiment session with ID {args.experiment_id} not found.{C.END}")
        sys.exit(1)
    
    # Convert raw tuple result to dictionary for easier access
    session_data = dict(zip(['id', 'title', 'start_time', 'end_time', 'context_json', 'final_summary', 'final_hash', 'status'], exp_session_raw[0]))
    session_start_time = session_data['start_time'].isoformat() if hasattr(session_data['start_time'], 'isoformat') else str(session_data['start_time'])
    
    # Ensure context_json is parsed correctly for safe access
    session_context = json.loads(session_data.get('context_json', '{}')) if isinstance(session_data.get('context_json'), str) else session_data.get('context_json', {})

    # Retrieve ScienceLog entries
    science_logs_raw = notebook.query_relational(
        f"SELECT id, timestamp, entry_type, data, supersedes_id, correction_reason "
        f"FROM ScienceLog WHERE session_id = {args.experiment_id} ORDER BY timestamp ASC"
    )
    
    # Retrieve TransactionLog entries
    transaction_logs_raw = notebook.query_relational(
        f"SELECT id, timestamp, raw_io "
        f"FROM TransactionLog WHERE session_id = {args.experiment_id} ORDER BY timestamp ASC"
    )

    # Format logs into a structured list of dicts for the LLM prompt
    formatted_science_logs = []
    for log_id, timestamp, entry_type, data_json, supersedes_id, correction_reason in science_logs_raw:
        ts_str = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
        formatted_science_logs.append({
            "log_id": log_id, "timestamp": ts_str, "type": entry_type,
            "data": json.loads(data_json), "supersedes": supersedes_id, "reason": correction_reason
        })
    
    formatted_transaction_logs = []
    for log_id, timestamp, raw_io in transaction_logs_raw:
        ts_str = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
        formatted_transaction_logs.append({
            "log_id": log_id, "timestamp": ts_str, "raw_io": raw_io
        })

    # --- Extract and Format Human-in-the-Loop Interactions ---
    hitl_rows = []
    for log in formatted_science_logs:
        log_id = log["log_id"]
        ts_str = log["timestamp"].split("T")[-1] if "T" in log["timestamp"] else log["timestamp"].split(" ")[-1]
        if "." in ts_str:
            ts_str = ts_str.split(".")[0]
            
        entry_type = log["type"]
        data = log["data"]
        
        if entry_type == "intent":
            content = data.get("goal") or data.get("intent") or ""
            hitl_rows.append(f"| {log_id} | {ts_str} | Instruction (Intent) | {content} |")
        elif entry_type == "note":
            content = data.get("message") or ""
            hitl_rows.append(f"| {log_id} | {ts_str} | Operator Note | {content} |")
        elif entry_type == "plan" and data.get("human_edits"):
            edits = data.get("human_edits")
            edits_formatted = []
            for edit in edits:
                action = edit.get("action", "")
                cmd = edit.get("cmd", "")
                rationale = edit.get("rationale", "")
                edits_formatted.append(f"{action.upper()} '{cmd}' ({rationale})")
            hitl_rows.append(f"| {log_id} | {ts_str} | Plan Modification | {'; '.join(edits_formatted)} |")

    if hitl_rows:
        human_interactions_md = (
            "| Log ID | Time | Type | Content |\n"
            "| :---: | :---: | :---: | :--- |\n" + "\n".join(hitl_rows)
        )
    else:
        human_interactions_md = "*No specific Human-in-the-Loop interactions or overrides were recorded.*"

    # --- Format Reagents List ---
    reagents_raw = session_context.get('reagents', {})
    if reagents_raw:
        reagents_list = "\n".join([f"*   **{k}:** {v}" for k, v in reagents_raw.items()])
    else:
        reagents_list = "*   *No reagents registered in session context.*"

    # Compile static replacements. Leave synthesis placeholders intact for LLM completion.
    replacements = {
        "{{ EXPERIMENT_TITLE }}": session_data.get('title', 'N/A') or "N/A",
        "{{ DATE }}": session_start_time.split('T')[0] if 'T' in session_start_time else session_start_time.split(' ')[0],
        "{{ SESSION_ID }}": str(session_data['id']),
        "{{ REAGENTS_LIST }}": reagents_list,
        "{{ HUMAN_INTERACTIONS }}": human_interactions_md
    }

    # If objective summary is pre-defined in DB context, replace it. Otherwise, let LLM synthesize it.
    if session_context.get('objective'):
        replacements["{{ OBJECTIVE_SUMMARY }}"] = session_context['objective']

    # Apply metadata replacements to the template content
    for key, value in replacements.items():
        template_content = template_content.replace(key, value)

    # Ask the user for extra context as fallback input
    print(f"\n{C.INFO}--- Experiment Context ---{C.END}")
    print("Please provide specific experimental details to aid the summary.")
    print("(e.g., 'This was a titration of Acetic Acid with NaOH using Universal Indicator')")
    user_context = input(f"{C.WARN}> {C.END}").strip()
    if not user_context:
        print(f"{C.WARN}No context provided. Proceeding with log data only.{C.END}")
        user_context = "No specific user context provided."

    # 4. Prepare Prompt for the LLM
    system_instruction = """You are an expert Laboratory Data Scientist. 
Your task is to write a formal, highly professional electronic laboratory notebook entry by completing the provided Markdown Template using a robotic execution log.

**GUIDELINES:**
- **Strictly follow the structure of the provided template.** Do not add, remove, or modify top-level markdown headers.
- **Synthesize Remaining Placeholders:** Populate the placeholders `{{ OBJECTIVE_SUMMARY }}`, `{{ CONNECTED_DEVICES }}`, `{{ PROCEDURAL_SUMMARY }}`, `{{ DATA_ANALYSIS }}`, `{{ REFLECTIONS }}`, and `{{ RECOMMENDATIONS }}` dynamically by replacing them in the template.
- **Objective Summary:** Formulate a clear, concise scientific objective based on the experiment name, context, and logged interactions.
- **Connected Devices:** Identify and list the physical hardware devices active during the run (e.g., robotic arms, colorimeters) by analyzing command structures in the logs.
- **Procedural Summary:** Write a high-quality, professional, step-by-step summary of the experimental run. Organize the description as logical laboratory phases rather than a raw sequential list of commands.
- **Data Analysis & Results:** Extract raw spectral data from 'observation' records in the Science Log. Format this data into tidy Markdown tables grouped logically (e.g., control tests, continuous variation series). Discuss visible trends, spectral absorption behaviors, and potential outliers/errors.
- **Reflections & Next Steps:** Formulate current thoughts on the outcome, identify potential data processing steps (such as blank subtraction and absorbance conversion), state any concerns or source of noise, and propose concrete recommendations/next steps for subsequent trials.
- **Tone:** Maintain a humble, professional, objective, and scholarly tone. Avoid overconfident or exaggerated language (do not use words like "perfectly", "flawlessly", or "100% correct").
"""

    user_prompt = f"""
--- USER CONTEXT ---
{user_context}

--- MARKDOWN TEMPLATE ---
{template_content}

--- DLN SESSION DATA ---
**Experiment Session Metadata:**
{json.dumps(session_data, indent=2)}

**Science Log Entries:**
{json.dumps(formatted_science_logs, indent=2)}

**Transaction Log Entries (recent 20):**
{json.dumps(formatted_transaction_logs[-20:], indent=2)}
"""

    # 5. Initialize Agent
    print(f"{C.INFO}Initializing Agent ({args.agent} / {args.model})...{C.END}")
    try:
        agent = LLMManager.get_agent(
            provider=args.agent, 
            model=args.model, 
            context=system_instruction
        )
    except Exception as e:
        print(f"{C.ERR}Failed to initialize agent: {e}{C.END}")
        sys.exit(1)

    # 6. Generate Summary
    print(f"{C.INFO}Generating report... (This may take a moment){C.END}")
    response = agent.prompt(user_prompt, use_history=False)

    if response:
        # 7. Save Output
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(response)
            print(f"\n{C.OK}Success! Report saved to: {args.output}{C.END}")
        except Exception as e:
            print(f"{C.ERR}Failed to write output file: {e}{C.END}")
    else:
        print(f"{C.ERR}Agent returned no response.{C.END}")

if __name__ == "__main__":
    main()