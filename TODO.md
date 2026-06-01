# List of things to think about.

## How to handle logging of referenced sessions.

**Context** When a prior session is referenced with `/set session <id>` it is logged in the dln under the current session id, which is fixed. Once a session is complete, it cannot be altered or appended. This data/history preservation strategy results in a query challenge if something in this new session needs to be found in the future.

**Options**

- Update queries to search for the "focus_session" key in the `context` entry type.
- Update session_id searches to be `IN (a, b, c)` instead of an equality. Also revise /session commands to be add/drop as opposed to set, which will modify that list
- Create a virtual experiment/meta-analysis style experiment

I'm leaning towards the listed session_id. I do not know how much needs to be changed (what references session_id presently)

## UX tweaks

- In run mode, we don't need to see the text of "Goal received" since we just typed it
- In action/planning mode, the reminder that run accepts a y is needed.
- Update world_model.json so that there is a template that gets stored for reference but the actual json file is .gitignored

## POSE

- ai_utils.py is performing the duties of the DeviceManager. It should be moved to enforce separation of concerns. the control_panel gui should be reviewed to ensure we have not repeated ourselves.
    - It's not clear than anything in ai_utils.py belongs in the ai folder. All of this work belongs to the device manager: connect_devices, get_instructions, and the world_model loading needs to be made available to ai and non-ai access, so this is a core feature - possibly a separate script to allow for future modification and generation assistance.
    - The device manager is the controller and should not be issuing print commands. It could be logging these responses.
- DeviceManager should be in charge of scanning for devices, connecting and disconnecting devices, returning information about the devices, and sending/receiving messages to/from devices.
- Make a decision on where to put information. we have the .env file and world_model.json along with hard coded defaults.  Too many places to cause an error.