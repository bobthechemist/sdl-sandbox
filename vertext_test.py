import sys
import time
import json
import re

# <<< FIX IS HERE: Using your actual agent implementation >>>
import temp.vertext_agent as myagent

from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message
from communicate.host_utilities import find_data_comports
from host_app.firmware_db import FIRMWARE_DATABASE, get_device_name

def get_instrument_list_for_ai():
    """Formats the FIRMWARE_DATABASE into a simple list of names for the AI."""
    instrument_names = set()
    for vid, mfg_info in FIRMWARE_DATABASE.items():
        for pid, product_name in mfg_info.get('products', {}).items():
            instrument_names.add(product_name)
    return sorted(list(instrument_names))

def find_device_port_by_name(target_name: str):
    """Scans for a connected device by its name from the firmware database."""
    print(f"Scanning for a connected '{target_name}'...")
    all_ports = find_data_comports()
    for port_info in all_ports:
        full_device_name = get_device_name(port_info['VID'], port_info['PID'])
        if target_name.lower() in full_device_name.lower():
            print(f"  [+] Found '{target_name}' on port {port_info['port']}")
            return port_info['port']
    return None

def send_command_and_wait(postman: SerialPostman, command_payload: dict, expected_status: str, timeout: int = 5):
    """Sends a command and waits for a specific response status."""
    message = Message.create_message(
        subsystem_name="AI_WORKFLOW",
        status="INSTRUCTION",
        payload=command_payload
    )
    postman.send(message.serialize())
    print(f"\nSENT --> {message.to_dict()}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        raw_response = postman.receive()
        if raw_response:
            try:
                response_msg = Message.from_json(raw_response)
                print(f"RECV <-- {response_msg.to_dict()}")
                if response_msg.status == expected_status:
                    return response_msg
            except (json.JSONDecodeError, ValueError):
                print(f"RECV RAW <-- {raw_response}")
        time.sleep(0.1)
    
    print(f"\nERROR: Timed out after {timeout}s waiting for a '{expected_status}' response.")
    return None

def main():
    """Main function to run the AI-driven workflow."""
    print("====== AI Dynamic Instrument Workflow Started ======")
    
    postman = None
    try:
        user_prompt = "what color do you see?"
        print(f"Human asks: '{user_prompt}'")

        # [Step 1] SELECT THE INSTRUMENT
        print("\n[Step 1] Choosing an instrument to answer the question...")
        instrument_list = get_instrument_list_for_ai()
        selector_context = (
            "You are a Selector agent. Your job is to select the single best instrument from a list to answer a user's question. "
            f"Here are the available instruments: {instrument_list}. "
            "You MUST respond with ONLY the name of the chosen instrument and nothing else."
        )
        selector_agent = myagent.Agent(context=selector_context)
        selector_prompt = f"Select one instrument to answer this question: '{user_prompt}'"
        
        chosen_instrument_name = selector_agent.prompt(selector_prompt).strip()
        print(f"Selector AI has chosen: '{chosen_instrument_name}'")

        if chosen_instrument_name not in instrument_list:
            raise RuntimeError(f"AI chose an invalid instrument '{chosen_instrument_name}'. Available: {instrument_list}")

        # [Step 2] CONNECT TO THE CHOSEN INSTRUMENT
        print(f"\n[Step 2] Connecting to '{chosen_instrument_name}'...")
        device_port = find_device_port_by_name(chosen_instrument_name)
        if not device_port:
            raise RuntimeError(f"The chosen instrument '{chosen_instrument_name}' is not connected.")

        postman_params = {"port": device_port, "baudrate": 115200, "timeout": 0.1, "protocol": "serial"}
        postman = SerialPostman(postman_params)
        postman.open_channel()
        time.sleep(2)
        postman.channel.reset_input_buffer()
        print(f"Connection to {device_port} established.")

        # [Step 3] QUERY DEVICE FOR COMMANDS
        print("\n[Step 3] Querying device for available commands...")
        help_payload = {"func": "help", "args": {}}
        help_response = send_command_and_wait(postman, help_payload, "DATA_RESPONSE")
        
        if not help_response:
            raise RuntimeError("Failed to get command list from device.")
            
        command_docs = help_response.payload.get('data', {})
        
        # [Step 4] PLAN THE ACTION
        planner_context = (
            "You are a Planner agent. Your sole purpose is to convert a user's request into a "
            "single, raw JSON command for an instrument. The JSON object MUST have a 'func' key and an 'args' key. "
            "Do not add any other text, explanations, or formatting.\n"
            f"Here are the available commands for the '{chosen_instrument_name}':\n"
            f"{json.dumps(command_docs, indent=2)}"
        )
        
        print("\n[Step 4] Initializing Planner agent and prompting for a command...")
        planner_agent = myagent.Agent(context=planner_context)
        ai_command_str = planner_agent.prompt(user_prompt)
        print(f"Planner AI responds with command: {ai_command_str}")

        match = re.search(r'```(json)?\s*({.*?})\s*```', ai_command_str, re.DOTALL)
        clean_json_str = match.group(2) if match else ai_command_str
        
        try:
            ai_command_payload = json.loads(clean_json_str)
        except json.JSONDecodeError:
            raise RuntimeError(f"Planner AI returned invalid JSON: {clean_json_str}")
        
        if "func" not in ai_command_payload:
            raise RuntimeError(f"Planner AI JSON is missing the required 'func' key: {ai_command_payload}")

        # [Step 5] EXECUTE THE ACTION
        print("\n[Step 5] Executing AI-generated command...")
        data_response = send_command_and_wait(postman, ai_command_payload, "DATA_RESPONSE")

        if not data_response:
            raise RuntimeError("Failed to get data from the device.")
            
        instrument_data = data_response.payload.get('data', {})
        print(f"Received data: {instrument_data}")
        
        # [Step 6] ANALYZE THE RESULTS
        print("\n[Step 6] Initializing Analyst agent and prompting for interpretation...")
        analyst_context = (
            "You are an Analyst agent. Your role is to interpret scientific data from a laboratory instrument "
            "and provide a clear, concise, natural-language answer to the user's original question."
        )
        analyst_agent = myagent.Agent(context=analyst_context)
        interpretation_prompt = (
            f"The original question was: '{user_prompt}'.\n"
            f"The '{chosen_instrument_name}' returned the following data: {instrument_data}.\n"
            "Based on this data, how would you answer the original question?"
        )
        final_answer = analyst_agent.prompt(interpretation_prompt)

        print("\n" + "="*50)
        print("          WORKFLOW COMPLETE")
        print("="*50)
        print(f"Initial Question: {user_prompt}")
        print(f"Chosen Instrument: {chosen_instrument_name}")
        print(f"Final Answer: {final_answer}")
        print("="*50)

    except Exception as e:
        print(f"\nFATAL ERROR during workflow: {e}")
    finally:
        if postman and postman.is_open:
            postman.close_channel()
            print("\nConnection closed.")

if __name__ == "__main__":
    main()