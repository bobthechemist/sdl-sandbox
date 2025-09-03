# firmware/diystirplate/handlers.py
# Device-specific commands

def handle_on(machine, payload):
    """
    Handles the device-specific 'on' command.
    DOC: Turns on the stirplate.
    ARGS:
      - None
    """
    try:
        machine.duty_cycle = 1
        machine.period = 1
        machine.go_to_state('Stirring')
    except Exception as e:
        machine.flags['error_message'] = str(e)
        machine.log.critical(f"Error in processing the function `on`: {e}")
        machine.got_to_state('Error')

def handle_off(machine, payload):
    """
    Handles the device-specific 'off' command.
    DOC: Turns on the stirplate.
    ARGS:
      - None
    """
    try:
        machine.duty_cycle = 0
        machine.pwm.value = False
        machine.log.info("Turning stirplate off")
        machine.go_to_state("Idle")
    except Exception as e:
        machine.flags['error_message'] = str(e)
        machine.log.critical(f"Error in processing the function `on`: {e}")
        machine.got_to_state('Error')