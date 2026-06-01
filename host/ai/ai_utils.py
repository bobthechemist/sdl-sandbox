# host/ai/ai_utils.py
import sys
import time
import queue
import json
from pathlib import Path

# Setup project root path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from host.core.device_manager import DeviceManager
from host.gui.console import C
from shared_lib.messages import Message

def load_world_from_file(filepath: str):
    """Loads a world model from a specified JSON file."""
    print(f"\n{C.INFO}[+] Loading world model from '{filepath}'...{C.END}")
    try:
        with open(filepath, 'r') as f:
            world_model = json.load(f)
        print(f"{C.OK}  -> World model loaded successfully.{C.END}")
        return world_model
    except FileNotFoundError:
        print(f"{C.ERR}  -> Error: World file not found at '{filepath}'.{C.END}")
        return None
    except json.JSONDecodeError as e:
        print(f"{C.ERR}  -> Error: Could not parse world file. Invalid JSON: {e}{C.END}")
        return None

