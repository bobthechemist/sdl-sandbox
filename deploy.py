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

# Try to import configurations from the central firmware database
try:
    from host.firmware_db import FIRMWARE_DATABASE
except ImportError:
    print(f"{C.ERR}FATAL: Could not import FIRMWARE_DATABASE from host/firmware_db.py{C.END}")
    sys.exit(1)

try:
    from host.firmware_db import FIRMWARE_DEPENDENCIES
except ImportError:
    print(f"{C.WARN}WARN: Could not import FIRMWARE_DEPENDENCIES from host/firmware_db.py. Defaulting to empty list.{C.END}")
    FIRMWARE_DEPENDENCIES = {}

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

def copy_newer_file(src: Path, dst: Path):
    """Copies a single file if the source is newer than the destination or if dst doesn't exist."""
    if dst.exists() and src.stat().st_mtime <= dst.stat().st_mtime:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def sync_path(src: Path, dst: Path):
    """Syncs a file or folder incrementally using copy_newer logic."""
    if src.is_file():
        copy_newer_file(src, dst)
    elif src.is_dir():
        shutil.copytree(src, dst, copy_function=copy_newer, dirs_exist_ok=True)

def find_dependency(dependency_name: str, search_paths: list[Path]):
    """
    Searches host directories for a specified CircuitPython dependency.
    Looks for a folder named <dependency_name>, a file named <dependency_name>.mpy,
    or a file named <dependency_name>.py.
    Returns (source_path, target_filename/directory_name) or (None, None).
    """
    for base_path in search_paths:
        if not base_path.is_dir():
            continue
        
        # 1. Check folder directory
        folder_path = base_path / dependency_name
        if folder_path.is_dir():
            return folder_path, dependency_name
            
        # 2. Check compiled .mpy file
        mpy_path = base_path / f"{dependency_name}.mpy"
        if mpy_path.is_file():
            return mpy_path, f"{dependency_name}.mpy"
            
        # 3. Check plain .py file
        py_path = base_path / f"{dependency_name}.py"
        if py_path.is_file():
            return py_path, f"{dependency_name}.py"
            
    return None, None

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
            if str(db_vid) == str(vid) and str(db_pid) == str(pid):
                return product_name
    return None

def get_dependencies_for_firmware(firmware_name: str) -> list[str]:
    """Retrieves list of dependency strings from database mapping, using normalization."""
    normalized_target = normalize_name(firmware_name).replace(" ", "_")
    for key, dependencies in FIRMWARE_DEPENDENCIES.items():
        if normalize_name(key).replace(" ", "_") == normalized_target:
            return dependencies
    return []

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

    # --- 1. Copy Core Project Libraries (Communicate and Shared Lib) ---
    print(f"{C.INFO}[+] Copying core Talos communication libraries...{C.END}")
    for name, relative_path in [('communicate', 'communicate'), ('shared_lib', 'shared_lib')]:
        src_dir = PROJECT_ROOT / relative_path
        dest_path = dest_lib_path / name
        print(f"  - Syncing '{name}' → {dest_path}")
        try:
            sync_path(src_dir, dest_path)
        except Exception as e:
            print(f"  - {C.WARN}WARN: Failed to sync core library '{name}': {e}{C.END}")

    # --- 2. Copy Target Subsystem & Common Libraries (Only) ---
    print(f"\n{C.INFO}[+] Copying requested target firmware module...{C.END}")
    dest_firmware_root = dest_lib_path / 'firmware'
    dest_firmware_root.mkdir(exist_ok=True)

    # Copy firmware/common
    try:
        print(f"  - Syncing 'firmware/common' → {dest_firmware_root / 'common'}")
        sync_path(PROJECT_ROOT / 'firmware' / 'common', dest_firmware_root / 'common')
    except Exception as e:
        print(f"  - {C.WARN}WARN: Failed to sync 'firmware/common': {e}{C.END}")

    # Copy targeted firmware folder (e.g., sidekick, colorimeter, buzzer_v1)
    try:
        print(f"  - Syncing 'firmware/{args.firmware_name}' → {dest_firmware_root / args.firmware_name}")
        sync_path(PROJECT_ROOT / 'firmware' / args.firmware_name, dest_firmware_root / args.firmware_name)
    except Exception as e:
        print(f"  - {C.WARN}WARN: Failed to sync 'firmware/{args.firmware_name}': {e}{C.END}")

    # --- 3. Copy Driver and Runtime Dependencies ---
    search_paths = [
        PROJECT_ROOT / 'firmware_lib'
    ]

    req_libs = get_dependencies_for_firmware(args.firmware_name)
    missing_libs = []

    if req_libs:
        print(f"\n{C.INFO}[+] Resolving external hardware dependencies from 'firmware_lib'...{C.END}")
        for lib in req_libs:
            src_path, target_name = find_dependency(lib, search_paths)
            if src_path:
                dest_path = dest_lib_path / target_name
                print(f"  - Copying dependency: '{target_name}' → {dest_path}")
                try:
                    sync_path(src_path, dest_path)
                except Exception as e:
                    print(f"  - {C.WARN}WARN: Failed to copy dependency '{lib}': {e}{C.END}")
            else:
                missing_libs.append(lib)

    # --- 4. If switching firmware, update root files boot.py and code.py ---
    if will_update_root_files:
        print(f"\n{C.INFO}[+] Updating root boot.py and code.py files for target configuration...{C.END}")
        try:
            boot_template_path = PROJECT_ROOT / 'firmware' / 'common' / 'boot.py'
            boot_template = boot_template_path.read_text()
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

    # Report any missing dependencies at the end
    if missing_libs:
        print(f"\n{C.WARN}⚠️  WARNING: The following external CircuitPython dependencies mapped in 'firmware_db.py' were not found in 'firmware_lib/':")
        for lib in missing_libs:
            print(f"  - {lib}")
        print(f"\nPlease place the missing dependency folders or matching .py/.mpy files inside the host dependency folder:")
        print(f"  - { (PROJECT_ROOT / 'firmware_lib').relative_to(PROJECT_ROOT) }/")
        print(f"Or manually install them on the target microcontroller's 'lib/' directory.{C.END}\n")

def same_device_check(args):
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