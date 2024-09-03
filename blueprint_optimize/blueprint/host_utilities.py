# type: ignore
from .utility import check_if_microcontroller

# Import appropriate modules based on the environment
if check_if_microcontroller():
    raise ImportError(f'This module is not intended to function on a microcontroller')
else:
    import adafruit_board_toolkit.circuitpython_serial

def find_data_comports():
    """
    Looks for circuit python data ports and returns a subset of information about the port, 
     such as port identification and the two ID values that can be modified.
    """
    ports = adafruit_board_toolkit.circuitpython_serial.data_comports()
    data = []
    for p in ports:
        #print(f"Found a device on {p.device}. (VID:{p.vid}, PID:{p.pid})")
        data.append({'port':p.device, 'VID':p.vid, 'PID':p.pid})
    return data