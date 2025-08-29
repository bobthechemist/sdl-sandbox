# type: ignore
"""
Utility functions relevant to the host (PC/MAC/LINUX) computer operating the software driven laboratory

Author(s): BoB LeSuer
"""
from ..shared_lib.utility import check_if_microcontroller

# Import appropriate modules based on the environment
if check_if_microcontroller():
    raise ImportError(f'This module is not intended to function on a microcontroller')
else:
    import adafruit_board_toolkit.circuitpython_serial

def find_data_comports():
    """
    Looks for CircuitPython data ports and returns a subset of information about the port.

    This function scans for CircuitPython data ports and collects information such as 
    port identification and the two ID values (VID and PID) that can be modified.

    Returns:
    --------
    list of dict:
        A list of dictionaries, each containing:
        - 'port': str, the device port.
        - 'VID': int, the vendor ID of the device.
        - 'PID': int, the product ID of the device.
    """
    ports = adafruit_board_toolkit.circuitpython_serial.data_comports()
    data = []
    for p in ports:
        data.append({'port': p.device, 'VID': p.vid, 'PID': p.pid})
    return data
