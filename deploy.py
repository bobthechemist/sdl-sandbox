import argparse
import sys
import os
import shutil
from pathlib import Path

# Add the project root to the Python path to allow importing from host_app
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from host_app.firmware_db import FIRMWARE_DATABASE
except ImportError:
    print("FATAL: Could not import FIRMWARE_DATABASE from host_app/firmware_db.py")
    print("Ensure the script is being run from the project's root directory.")
    sys.exit(1)

# Simple color class for better terminal output
class C:
    OK = '\033[92m'
    WARN = '\033[93m'
    ERR = '\033[91m'
    INFO = '\033[94m'
    END = '\033[0m'

def find_vid_pid_by_name(firmware_name: str):
    """Searches the FIRMWARE_DATABASE and returns the VID/PID for a given name."""
    search_name = firmware_name.lower().replace("_", " ").replace("-", " ")
    for vid, manufacturer_info in FIRMWARE_DATABASE.items():
        for pid, product_name in manufacturer_info.get('products', {}).items():
            if search_name in product_name.lower().replace("_", " ").replace("-", " "):
                return vid, pid
    return None, None

def copy_newer(src, dst, *, follow_symlinks=True):
    """
    A custom copy function for shutil.copytree that only copies if the
    source file is newer than the destination.
    """
    if Path(dst).exists() and Path(src).stat().st_mtime <= Path(dst).stat().st_mtime:
        return dst  # Skip copying
    return shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

def deploy(args):
    """Main deployment function."""
    # --- 1. Validation ---
    print(f"{C.INFO}[*] Validating inputs...{C.END}")
    dest_drive = Path(args.drive)
    if not dest_drive.exists() or not dest_drive.is_dir():
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

    # --- 2. Print Summary ---
    mode_desc = "Update (only newer files)" if args.update else "Full (clean)"
    print("\n" + "="*50)
    print(" Deploying to CircuitPython Device")
    print("-"*50)
    print(f"  {'Drive:':<12} {dest_drive}")
    print(f"  {'Firmware:':<12} {args.firmware_name}")
    print(f"  {'VID/PID:':<12} {vid} / {pid}")
    print(f"  {'Mode:':<12} {mode_desc}")
    print("="*50 + "\n")
    
    # --- 3. Deployment Logic ---
    dest_lib_path = dest_drive / 'lib'
    dest_lib_path.mkdir(exist_ok=True)
    
    dirs_to_copy = {
        'shared_lib': PROJECT_ROOT / 'shared_lib',
        'communicate': PROJECT_ROOT / 'communicate',
        'firmware/common': PROJECT_ROOT / 'firmware' / 'common',
        f'firmware/{args.firmware_name}': firmware_src_dir
    }

    for name, src_path in dirs_to_copy.items():
        dest_path = dest_lib_path / name
        print(f"{C.INFO}[+] Processing '{name}'...{C.END}")
        
        if args.update:
            # Update mode: Copy newer files, create directories if they don't exist.
            # Requires Python 3.8+ for dirs_exist_ok=True
            print(f"  - Updating files in {dest_path}")
            shutil.copytree(src_path, dest_path, copy_function=copy_newer, dirs_exist_ok=True)
        else:
            # Clean mode: Remove the old directory first.
            if dest_path.exists():
                print(f"  - Removing old version at {dest_path}")
                shutil.rmtree(dest_path)
            print(f"  - Copying files to {dest_path}")
            shutil.copytree(src_path, dest_path)

    # --- 4. Customize and Deploy Root Files ---
    print(f"{C.INFO}[+] Processing root files...{C.END}")
    
    # Customize boot.py
    boot_template = (PROJECT_ROOT / 'firmware' / 'common' / 'boot.py').read_text()
    boot_content = boot_template.replace('_VID_PLACEHOLDER_', str(vid))
    boot_content = boot_content.replace('_PID_PLACEHOLDER_', str(pid))
    (dest_drive / 'boot.py').write_text(boot_content)
    print(f"  - Wrote customized boot.py (VID={vid}, PID={pid})")
    
    # Customize code.py
    code_template = (PROJECT_ROOT / 'firmware' / 'common' / 'code.py').read_text()
    code_content = code_template.replace('SUBSYSTEM', args.firmware_name)
    (dest_drive / 'code.py').write_text(code_content)
    print(f"  - Wrote customized code.py (imports '{args.firmware_name}')")

    print(f"\n{C.OK}{'='*50}\n Deployment complete!\n{'='*50}{C.END}")

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
    
    # Check for Python version dependency for update mode
    if args.update and sys.version_info < (3, 8):
        print(f"{C.ERR}ERROR: Update mode (-u) requires Python 3.8 or newer.{C.END}")
        sys.exit(1)
        
    deploy(args)

if __name__ == "__main__":
    main()