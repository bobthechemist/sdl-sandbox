# firmware/fake/handlers.py
# Device-specific commands

def handle_blink(machine, payload):
    """
    Handles the device-specific 'blink' command.
    DOC: Blinks the onboard LED a specified number of times.
    ARGS:
      - count (integer)
    """

    args = payload.get("args",{})
    
    count = args.get("count",3)
    on_time = args.get("on_time", 0.4)
    off_time = args.get("off_time", 0.1)
    try:
        machine.flags['blink_count'] = count
        machine.flags['blink_on_time'] = on_time
        machine.flags['blink_off_time'] = off_time
        machine.log.info(f"Blink request received for {count} times with ON={on_time} and OFF={off_time}.")
        machine.go_to_state('Blinking')
    except Exception as e:
        machine.log.error(f"Problem parsing args: {args}. Error raised is {e}")
        machine.go_to_state('Idle')