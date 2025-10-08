import argparse
import sys
from pathlib import Path
from host.core.discovery import associate_drive_to_device
from host.gui.console import C
import shutil
import time


# Add the project root to the Python path to allow importing from host_app
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from host.firmware_db import FIRMWARE_DATABASE
except ImportError:
    print(f"{C.ERR}FATAL: Could not import FIREWARE_DATABASE{C.END}")
    sys.exit(1)

def find_vid_pid_by_name(firmware_name: str):
    """Searches the FIRMWARE_DATABASE and returns the VID/PID for a given name."""
    search_name = firmware_name.lower().replace("_", " ").replace("-", " ")
    for vid, manufacturer_info in FIRMWARE_DATABASE.items():
        for pid, product_name in manufacturer_info.get('products', {}).items():
            if search_name in product_name.lower().replace("_", " ").replace("-", " "):
                return vid, pid
    return (None, None)

def copy_newer(src, dst, *, follow_symlinks=True):
    """
    A custom copy function for shutil.copytree that only copies if the
    source file is newer than the destination.
    """
    if Path(dst).exists() and Path(src).stat().st_mtime <= Path(dst).stat().st_mtime:
        return dst  # Skip copying
    return shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

def robust_rmtree(path, retries=5, delay=0.5):
    for i in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError as e:
            if e.winerror == 5:
                print(f"PermissionError on {path}, retrying... ({i+1}/{retries})")
                time.sleep(delay)
            else:
                raise
    print(f"WARNING: Could not delete {path} after {retries} retries.")


def normalize_name(name: str) -> str:
    """Normalize firmware/product names for reliable comparisons."""
    return name.lower().replace("_", " ").replace("-", " ").strip()

def get_firmware_name_by_vid_pid(vid, pid):
    """Reverse-lookup product name from FIRMWARE_DATABASE using VID/PID.
    Returns None if not found.
    """
    for db_vid, manufacturer_info in FIRMWARE_DATABASE.items():
        products = manufacturer_info.get('products', {})
        for db_pid, product_name in products.items():
            # Compare as strings to be robust vs ints/strs
            if str(db_vid) == str(vid) and str(db_pid) == str(pid):
                return product_name
    return None

def deploy(args):
    print(f"{C.INFO}[*] Validating inputs...{C.END}")
    dest_drive = Path(args.drive).resolve()
    if not dest_drive.is_dir():
        print(f"{C.ERR}ERROR: Destination drive '{dest_drive}' does not exist.{C.END}")
        return

    firmware_src_dir = PROJECT_ROOT / 'firmware' / args.firmware_name
    if not firmware_src_dir.is_dir():
        print(f"{C.ERR}ERROR: Firmware '{args.firmware_name}' not found at '{firmware_src_dir}'{C.END}")
        return

    vid, pid = find_vid_pid_by_name(args.firmware_name)
    if not vid or not pid:
        print(f"{C.ERR}ERROR: Could not find VID/PID for '{args.firmware_name}' in firmware_db.py.{C.END}")
        return

    # --- Identify current device firmware (if possible) ---
    device_info = None
    try:
        device_info = associate_drive_to_device(args.drive)
    except Exception:
        # keep device_info as None if detection fails
        device_info = None

    current_firmware_name = None
    if device_info:
        try:
            cur_vid = device_info.get("VID")
            cur_pid = device_info.get("PID")
            current_firmware_name = get_firmware_name_by_vid_pid(cur_vid, cur_pid)
        except Exception:
            current_firmware_name = None

    # Decide whether this is a same-firmware update or a firmware switch
    requested = normalize_name(args.firmware_name)
    detected = normalize_name(current_firmware_name) if current_firmware_name else None

    switching_firmware = (detected is None) or (detected != requested)

    # If switching (unknown or different firmware), prompt user to confirm
    if switching_firmware:
        detected_display = current_firmware_name or "<unknown>"
        prompt = (
            f"{C.WARN}WARNING:{C.END} Device appears to be running '{detected_display}'.\n"
            f"You are about to install '{args.firmware_name}' to {dest_drive}.\n"
            f"Do you want to continue? [y/N]: "
        )
        try:
            resp = input(prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{C.INFO}Aborting deployment by user request.{C.END}")
            return
        if resp not in ("y", "yes"):
            print(f"{C.INFO}Aborting deployment by user request.{C.END}")
            return
        will_update_root_files = True
    else:
        # same firmware — just update libraries, do not touch root files
        will_update_root_files = False
        print(f"{C.INFO}Device firmware matches '{args.firmware_name}' — performing in-place update (no root file changes).{C.END}")

    # --- Print summary ---
    mode_desc = "Update (same firmware)" if not will_update_root_files else "Install/Switch (will update code.py and boot.py)"
    print("\n" + "="*50)
    print(" Deploying to CircuitPython Device")
    print("-"*50)
    print(f"  {'Drive:':<12} {dest_drive}")
    print(f"  {'Firmware:':<12} {args.firmware_name}")
    print(f"  {'VID/PID:':<12} {vid} / {pid}")
    print(f"  {'Mode:':<12} {mode_desc}")
    print("="*50 + "\n")

    # --- Ensure lib folder exists ---
    dest_lib_path = dest_drive / 'lib'
    dest_lib_path.mkdir(exist_ok=True)

    dirs_to_copy = {
        'firmware': PROJECT_ROOT / 'firmware',
        'communicate': PROJECT_ROOT / 'communicate',
        'shared_lib': PROJECT_ROOT / 'shared_lib'
    }

    # --- Copy files (always: only copy newer files or non-existent ones) ---
    print(f"{C.INFO}[+] Copying libraries and modules (only newer or missing files)...{C.END}")
    for name, src_path in dirs_to_copy.items():
        dest_path = dest_lib_path / name
        print(f"  - Syncing '{name}' → {dest_path}")
        try:
            # copytree with copy_function=copy_newer and dirs_exist_ok=True will
            # only copy files that are newer (as defined in copy_newer).
            shutil.copytree(src_path, dest_path, copy_function=copy_newer, dirs_exist_ok=True)
        except Exception as e:
            # don't abort entirely on single copy errors; show message and continue.
            print(f"  - {C.WARN}WARN: Failed to fully copy '{name}': {e}{C.END}")

    # --- If switching firmware, update root files boot.py and code.py ---
    if will_update_root_files:
        print(f"{C.INFO}[+] Updating root files for new firmware...{C.END}")
        try:
            boot_template_path = PROJECT_ROOT / 'firmware' / 'common' / 'boot.py'
            boot_template = boot_template_path.read_text()
            # Replace placeholders — adjust tokens here if your templates differ
            boot_content = boot_template.replace('vid=808', f'vid={vid}').replace('pid=808', f'pid={pid}')
            (dest_drive / 'boot.py').write_text(boot_content)
            print(f"  - Wrote customized boot.py (VID={vid}, PID={pid})")
        except FileNotFoundError:
            print(f"  - {C.WARN}WARN: Missing 'firmware/common/boot.py' template. Skipping.{C.END}")
        except Exception as e:
            print(f"  - {C.WARN}WARN: Could not write boot.py: {e}{C.END}")

        try:
            code_template_path = PROJECT_ROOT / 'firmware' / 'common' / 'code.py'
            code_template = code_template_path.read_text()
            code_content = code_template.replace('SUBSYSTEM', args.firmware_name)
            (dest_drive / 'code.py').write_text(code_content)
            print(f"  - Wrote customized code.py (firmware={args.firmware_name})")
        except FileNotFoundError:
            print(f"  - {C.WARN}WARN: Missing 'firmware/common/code.py' template. Skipping.{C.END}")
        except Exception as e:
            print(f"  - {C.WARN}WARN: Could not write code.py: {e}{C.END}")

    print(f"\n{C.OK}{'='*50}\n Deployment complete!\n{'='*50}{C.END}")

def same_device_check(args):
    # Get the vid/pid tuple from the database
    db_vid_pid = find_vid_pid_by_name(args.firmware_name)
    device_info = associate_drive_to_device(args.drive)
    if not device_info:
        print(f"{C.WARN}WARN: Could not identify device on drive {args.drive}. Cannot verify firmware match.{C.END}")
        return False
    dev_vid_pid = (int(device_info['VID']), int(device_info['PID']))
    return db_vid_pid == dev_vid_pid

def main():
    """Parses command-line arguments and runs the deployment."""
    parser = argparse.ArgumentParser(
        description="Deploys firmware to a CircuitPython microcontroller.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("drive", help="The path to the CIRCUITPY drive (e.g., G: or /media/user/CIRCUITPY).")
    parser.add_argument("firmware_name", help="The name of the firmware to deploy (e.g., sidekick).")
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="Enable fast update mode. Only copies newer files without deleting old ones."
    )
    args = parser.parse_args()

    deploy(args)

if __name__ == "__main__":
    main()