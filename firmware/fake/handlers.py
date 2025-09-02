# firmware/fake/handlers.py
# Device-specific commands

def handle_blink(machine, payload):
    """
    Handles the device-specific 'blink' command.
    DOC: Blinks the onboard LED a specified number of times.
    ARGS:
      - count (integer, default: 1)
    """
    try:
        count = int(payload.get("args", [1])[0])
    except (ValueError, IndexError):
        count = 1
    
    machine.flags['blink_count'] = count
    machine.log.info(f"Blink request received for {count} times.")
    machine.go_to_state('Blinking')