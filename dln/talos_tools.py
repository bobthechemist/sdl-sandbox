# dln/talos_tools.py
import json
from typing import List, Dict, Any

# EXAMPLE USAGE
# from dln import DigitalLabNotebook, get_human_narrative_trail
# import json
# nb = DigitalLabNotebook(db_path=".talos/lab_notebook.db")
# trail = get_human_narrative_trail(nb, session_id=42)

def get_human_narrative_trail(notebook, session_id: int) -> List[Dict[str, Any]]:
    """
    Queries the ScienceLog for a chronological trail of human-driven actions,
    manual notes, and edited plans for a specific experiment session.
    
    This helper encapsulates SQLite JSON extraction mechanics, returning native
    Python objects rather than raw JSON strings.
    
    Args:
        notebook: An instantiated DigitalLabNotebook database connector.
        session_id: The ID of the experimental session to query.
        
    Returns:
        A list of dictionaries, each representing a structured narrative event.
    """
    # Force integer casting on input for security and type safety
    safe_session_id = int(session_id)

    # Standard SQL query utilizing SQLite JSON extension functions
    sql = f"""
    SELECT 
        id,
        session_id,
        timestamp,
        entry_type,
        CASE 
            WHEN entry_type = 'intent' THEN json_extract(data, '$.goal')
            WHEN entry_type = 'note'   THEN json_extract(data, '$.message')
            WHEN entry_type = 'plan'   THEN json_extract(data, '$.intent')
        END AS user_intent_or_message,
        CASE 
            WHEN entry_type = 'plan' THEN json_extract(data, '$.human_edits')
            ELSE NULL 
        END AS human_edits,
        CASE 
            WHEN entry_type = 'plan' THEN json_extract(data, '$.final_plan')
            ELSE NULL 
        END AS final_executed_plan
    FROM 
        ScienceLog
    WHERE 
        session_id = {safe_session_id}
        AND (
            entry_type IN ('intent', 'note')
            OR (
                entry_type = 'plan' 
                AND json_array_length(data, '$.human_edits') > 0
            )
        )
    ORDER BY 
        timestamp ASC;
    """
    
    raw_rows = notebook.query_relational(sql)
    parsed_trail = []

    for row in raw_rows:
        row_id, sess_id, timestamp, entry_type, message, raw_edits, raw_plan = row
        
        # Safely deserialize SQLite JSON string representations back into Python objects
        human_edits = None
        if raw_edits:
            try:
                human_edits = json.loads(raw_edits)
            except (json.JSONDecodeError, TypeError):
                human_edits = raw_edits  # Fallback to raw string if parsing fails

        final_plan = None
        if raw_plan:
            try:
                final_plan = json.loads(raw_plan)
            except (json.JSONDecodeError, TypeError):
                final_plan = raw_plan

        parsed_trail.append({
            "id": row_id,
            "session_id": sess_id,
            "timestamp": timestamp,
            "entry_type": entry_type,
            "message": message,
            "human_edits": human_edits,
            "final_executed_plan": final_plan
        })

    return parsed_trail