import time
import logging
from host.core.device_manager import DeviceManager
from host.firmware_db import get_device_name
from shared_lib.messages import Message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)-22s] %(levelname)-8s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

def run_backend_test():
    log.info("--- Starting Phase 2 Backend Test ---")
    
    manager = DeviceManager()
    manager.start()

    available_devices = manager.scan_for_devices()
    if not available_devices:
        log.error("No devices found. Cannot proceed with the test.")
        manager.stop()
        return

    device_info = available_devices[0]
    port, vid, pid = device_info['port'], device_info['VID'], device_info['PID']
    log.info(f"Found device: {get_device_name(vid, pid)} on port {port}")

    if not manager.connect_device(port, vid, pid):
        log.error(f"Failed to connect to {port}.")
        manager.stop()
        return

    time.sleep(1)
    device_model = manager.devices.get(port)
    if not device_model:
        log.error("Device model was not created correctly in the manager.")
        manager.stop()
        return
        
    # CORRECTED: Access attributes directly
    log.info(f"Initial Device State: Connected={device_model.is_connected}, State='{device_model.current_state}'")

    log.info("\n--- Sending 'get_info' command ---")
    get_info_message = Message.create_message("HOST_TEST", "INSTRUCTION", payload={"func": "get_info", "args": {}})
    manager.send_message(port, get_info_message)

    log.info("--- Sending 'help' command ---")
    help_message = Message.create_message("HOST_TEST", "INSTRUCTION", payload={"func": "help", "args": {}})
    manager.send_message(port, help_message)
    
    log.info("Waiting 5 seconds for responses to be processed...")
    time.sleep(5)

    log.info("\n--- Verifying Final Device Model State ---")
    
    # CORRECTED: Access attributes directly
    fw_name = device_model.firmware_name
    fw_version = device_model.version
    current_state = device_model.current_state
    
    log.info(f"Firmware Name: {fw_name}")
    log.info(f"Version:       {fw_version}")
    log.info(f"Current State: {current_state}")

    num_commands = len(device_model.supported_commands)
    log.info(f"Supported Commands Found: {num_commands}")
    if num_commands > 0:
        log.info(f"Example command: 'ping' -> {device_model.supported_commands.get('ping')}")

    success = True
    if fw_name == "?" or fw_name == "N/A":
        log.error("VALIDATION FAILED: Firmware Name was not updated.")
        success = False
    if num_commands == 0:
        log.error("VALIDATION FAILED: Supported Commands list is empty.")
        success = False

    if success:
        log.info("\n--- VALIDATION PASSED: The Device model was updated correctly. ---")
    else:
        log.warning("\n--- VALIDATION FAILED: See errors above. ---")

    log.info("\n--- Tearing down connection ---")
    manager.stop()
    log.info("--- Test Complete ---")

if __name__ == "__main__":
    run_backend_test()