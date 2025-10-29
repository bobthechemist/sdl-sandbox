# host/calibration/pump_calibration.py
import argparse
import sys
import time
from pathlib import Path
import queue

# Add the project root to the Python path to allow importing from the host package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from host.core.device_manager import DeviceManager
from shared_lib.messages import Message
from host.firmware_db import get_device_name
from host.gui.console import C

def find_sidekick_device(manager: DeviceManager):
    """Scans for devices and returns the info for the first Sidekick found."""
    print(f"{C.INFO}Scanning for a connected Sidekick...{C.END}")
    for dev_info in manager.scan_for_devices():
        friendly_name = get_device_name(dev_info['VID'], dev_info['PID'])
        if 'sidekick' in friendly_name.lower():
            dev_info['friendly_name'] = friendly_name
            print(f"{C.OK}Found Sidekick ({friendly_name}) at {dev_info['port']}{C.END}")
            return dev_info
    print(f"{C.ERR}Error: Could not find a connected Sidekick device.{C.END}")
    return None

def parse_pump_volumes(raw_args: list[str]) -> list[float]:
    """
    Parses a list of string arguments into exactly four float values for the pumps.
    Handles both space-separated and comma-separated inputs.
    """
    volumes = []
    for arg in raw_args:
        parts = [part.strip() for part in arg.split(',') if part.strip()]
        volumes.extend(parts)
    
    if len(volumes) != 4:
        raise argparse.ArgumentTypeError(f"Exactly 4 volume arguments are required, but {len(volumes)} were provided.")
    
    try:
        return [float(v) for v in volumes]
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid volume value: {e}. All volumes must be numbers.")

def wait_for_dispense_completion(manager: DeviceManager, port: str, timeout: int = 120) -> bool:
    """
    Waits for the 'dispense completed' SUCCESS message from the device.
    Returns True if the message is received, False on timeout.
    """
    start_time = time.time()
    expected_text = "Sequence dispense completed successfully"
    print(f"  -> Waiting for completion signal (timeout: {timeout}s)...")
    
    while time.time() - start_time < timeout:
        try:
            # Check the central queue for new messages
            msg_type, msg_port, msg_data = manager.incoming_message_queue.get_nowait()
            
            # Ensure the message is from the correct device and has the right status
            if msg_port == port and msg_data.status == "SUCCESS":
                payload = msg_data.payload
                # Check the content of the success message
                if isinstance(payload, dict) and expected_text in payload.get("message", ""):
                    print(f"{C.OK}  -> Done.{C.END}")
                    return True
                    
        except queue.Empty:
            # No message in the queue, wait a moment before trying again
            time.sleep(0.1)
            
    print(f"{C.ERR}  -> Timed out waiting for the device to confirm completion.{C.END}")
    return False

def main():
    """Main script to connect to the Sidekick and dispense calibration volumes."""
    parser = argparse.ArgumentParser(
        description="A script to dispense specified volumes from the Sidekick's four pumps for calibration.",
        epilog="Example usage: python pump_calibration.py 150 360,200 900"
    )
    parser.add_argument(
        "volumes",
        nargs='+',
        help="Four volume values (in uL) for pumps 1-4. Can be space- or comma-separated."
    )
    
    try:
        args = parser.parse_args()
        pump_volumes = parse_pump_volumes(args.volumes)
    except argparse.ArgumentTypeError as e:
        print(f"{C.ERR}Argument Error: {e}{C.END}")
        parser.print_help()
        sys.exit(1)

    print(f"{C.OK}====== Sidekick Pump Calibration Script ======{C.END}")
    print(f"Target Volumes (uL) -> P1:{pump_volumes[0]}, P2:{pump_volumes[1]}, P3:{pump_volumes[2]}, P4:{pump_volumes[3]}")

    manager = DeviceManager()
    manager.start()
    
    sidekick_info = find_sidekick_device(manager)
    if not sidekick_info:
        manager.stop(); return

    port = sidekick_info['port']
    if not manager.connect_device(port, sidekick_info['VID'], sidekick_info['PID']):
        print(f"{C.ERR}Failed to establish a connection with the Sidekick on port {port}.{C.END}")
        manager.stop(); return

    try:
        print("\n" + "="*50)
        input(f"{C.WARN}Press [Enter] when you are ready to dispense...{C.END}")
        print("="*50 + "\n")

        for i, volume in enumerate(pump_volumes):
            pump_id = f"p{i+1}"
            if volume > 0:
                print(f"[*] Dispensing {volume} uL from pump {i+1} ({pump_id})...")
                
                dispense_payload = {"func": "dispense", "args": {"pump": pump_id, "vol": float(volume)}}
                dispense_message = Message(subsystem_name="HOST_PUMP_CALIBRATOR", status="INSTRUCTION", payload=dispense_payload)
                manager.send_message(port, dispense_message)
                
                # Wait for the confirmation message before continuing the loop
                if not wait_for_dispense_completion(manager, port):
                    print(f"{C.ERR}Aborting routine due to timeout.{C.END}")
                    break # Exit the loop if a timeout occurs
            else:
                print(f"{C.WARN}Skipping pump {i+1}.")

        print(f"\n{C.OK}Dispensing routine complete.{C.END}")

    except KeyboardInterrupt:
        print(f"\n{C.INFO}Script interrupted by user.{C.END}")
    except Exception as e:
        print(f"\n{C.ERR}An unexpected error occurred: {e}{C.END}")
    finally:
        print("\nShutting down device manager...")
        manager.stop()
        print("Script finished.")

if __name__ == "__main__":
    main()