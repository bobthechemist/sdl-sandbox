# type: ignore
"""
Utility functions relevant to the host (PC/MAC/LINUX) computer operating the software driven laboratory

Author(s): BoB LeSuer
"""

#TODO: Consider moving this to host and expand its role as utility functions for the host.

from shared_lib.utility import check_if_microcontroller
import os
import re

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


def associate_drive_to_device(drive_path: str) -> dict | None:

    boot_py_path = os.path.join(drive_path, "boot.py")
    code_py_path = os.path.join(drive_path, "code.py")

    try:
        with open(boot_py_path, 'r') as f:
            boot_content = f.read()
        with open(code_py_path, 'r') as f:
            code_content = f.read()
    except FileNotFoundError:
        # Requisite files - boot.py and code.py are not - present.
        return None
    
    vid_match = re.search(r"vid\s*=\s*(0x[0-9a-fA-F]+|\d+)", boot_content)
    pid_match = re.search(r"pid\s*=\s*(0x[0-9a-fA-F]+|\d+)", boot_content)
    firmware_match = re.search(r"from\s+firmware\.(\w+)\s+import\s+machine", code_content)

    if not (vid_match and pid_match and firmware_match):
        return None

    boot_vid = int(vid_match.group(1), 0)
    boot_pid = int(pid_match.group(1), 0)
    firmware_name = firmware_match.group(1)

    for device in find_data_comports():
        if device.get('VID') == boot_vid and device.get('PID') == boot_pid:
            device['path'] = drive_path
            device['firmware'] = firmware_name
            return device
            
    return None


