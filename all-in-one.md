## .

### .gitignore

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#pdm.lock
#   pdm stores project-wide configurations in .pdm.toml, but it is recommended to not include it
#   in version control.
#   https://pdm.fming.dev/latest/usage/project/#working-with-version-control
.pdm.toml
.pdm-python
.pdm-build/

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#  and can be added to the global gitignore or merged into this file.  For a more nuclear
#  option (not recommended) you can uncomment the following to ignore the entire idea folder.
#.idea/

# BoB puts a lot of junk in the temp folder so let's ignore that
temp/
```

### README.md

```markdown
# Project: Self-Driving Laboratory Framework

This project provides a robust software framework for creating a **Self-Driving Laboratory**—a suite of microcontroller-driven scientific instruments controlled by a host computer. The architecture is designed for scalability, reliability, and ease of development, allowing new instruments to be integrated quickly and efficiently.

The framework is built around a state-machine-based design philosophy, which helps manage complexity, prevent bugs, and create responsive, non-blocking instruments.

## Core Concepts

The entire system is built on a few key architectural patterns that ensure consistency and reliability across all instruments.

### 1. Host-Device Architecture
The system operates on a classic host-device model:
-   **Host Computer:** A PC (Windows/macOS/Linux) runs the primary control software. It sends commands, receives data, and orchestrates complex experimental workflows.
-   **Microcontroller Devices:** Each scientific instrument is powered by a CircuitPython-compatible microcontroller. These devices run firmware that executes commands, controls hardware (pumps, motors, sensors), and reports back status and data.

### 2. State Machine-Driven Firmware
Each instrument's firmware is built as a **finite state machine**. This means at any given moment, the instrument is in one, and only one, well-defined state (e.g., `Initializing`, `Idle`, `Dispensing`, `Error`).
-   This logic is managed by the `StateMachine` and `State` classes found in `blueprint/statemachine.py`.
-   This approach prevents conflicting operations and makes the instrument's behavior predictable and easy to debug.

### 3. Message-Based Communication
All communication between the host and the devices occurs via simple, human-readable JSON messages sent over a serial connection.
-   A standard message follows this structure:
    ```json
    {
        "subsystem_name": "HOST",
        "status": "INSTRUCTION",
        "meta": {},
        "payload": {
            "func": "blink",
            "args": ["3"]
        }
    }
    ```
-   The `status` field is critical and can be `INSTRUCTION`, `SUCCESS`, `PROBLEM`, `HEARTBEAT`, etc.
-   This protocol is managed by the **`Postman`** classes (`communicate/serial_postman.py` for the host, `communicate/circuitpython_postman.py` for the device), which handle the low-level details of sending and receiving data.

## Project Structure

The repository is organized into several key directories:

```
.
├── .gitignore
├── deploy_firmware.bat       # Windows script to deploy firmware to a device
├── requirements.txt          # Python dependencies for the host
├── run_fake_device_test.py   # Example host script to test communication
│
├── blueprint/                # Source code for instrument "blueprints" (firmware)
│   ├── statemachine.py       # Core state machine classes
│   ├── communicator.py       # Low-level serial communication handler
│   ├── messages.py           # Message creation and buffer management
│   └── subsystems/           # Implementations for specific instruments
│       ├── demo.py
│       ├── sidekick.py
│       └── stirplate.py
│
├── communicate/              # Communication logic for host and device
│   ├── postman.py            # Base class for the "Postman" communication pattern
│   ├── serial_postman.py     # Host-side serial implementation
│   ├── circuitpython_postman.py # Device-side CircuitPython implementation
│   ├── secretary.py          # High-level message routing and management
│   └── host_utilities.py     # Helper functions for the host computer
│
└── docs/                     # Design documents and guides
    ├── socratic_design_guidelines.md   # Philosophy and process for designing new instruments
    └── AI assistent instrument design.md # Template for AI-assisted firmware generation
```

## Getting Started

Follow these steps to set up the host environment, deploy firmware to a device, and run a test.

### 1. Prerequisites
-   Python 3.8+
-   A CircuitPython-compatible microcontroller board (e.g., Raspberry Pi Pico, Adafruit Feather).
-   Your device flashed with the latest version of CircuitPython.

### 2. Host Setup
First, clone the repository and install the required Python packages.
```bash
git clone <your-repository-url>
cd <your-repository-name>
pip install -r requirements.txt
```

### 3. Deploying Firmware to a Device
The project includes a utility script to easily deploy the firmware and necessary libraries to your CircuitPython device.

1.  **Connect your CircuitPython device** to your computer. It should appear as a USB drive named `CIRCUITPY`.
2.  **Note the drive letter** assigned to it (e.g., `G:`).
3.  Open a command prompt or terminal and run the deployment script, passing the drive letter as an argument.

    **Note:** The `deploy_firmware.bat` script is written to copy directories named `firmware`, `communicate`, and `shared_lib`. Based on the project structure, you will be deploying the contents of the `blueprint`, `communicate`, and any shared library code. You may need to adjust the script or your folder structure accordingly. For this guide, we'll assume the intent is to deploy the instrument logic.

    ```bash
    # Example for a device on drive G:
    deploy_firmware.bat G
    ```
    The script will create a `lib` folder on the device (if it doesn't exist) and copy the necessary firmware files into it.

### 4. Running the Host Test Application
The `run_fake_device_test.py` script provides a simple way to test the communication between the host and a device running compatible firmware (like the one in `blueprint/subsystems/demo.py`).

1.  Ensure your device is connected and has the firmware deployed.
2.  Run the script from your terminal:
    ```bash
    python run_fake_device_test.py
    ```

You should see output indicating that the host has found the device, opened a connection, and is periodically sending a `blink` command and listening for responses.

**Example Output:**
```
--- SDL Host Live Test ---

Found device at: COM15
Serial port opened successfully. Listening for messages...
Press Ctrl+C to exit.

Sending blink command...
SENT --> [INSTRUCTION] {'subsystem_name': 'HOST', 'status': 'INSTRUCTION', 'meta': {...}, 'payload': {'func': 'blink', 'args': ['3']}}

RECEIVED <-- [SUCCESS] {'subsystem_name': 'DEMO', 'status': 'SUCCESS', 'meta': {...}, 'payload': 'Blink command acknowledged'}
```

## Creating a New Instrument

This framework is designed to be easily extended with new instruments. The core philosophy and process are detailed in the `docs/` directory.

The recommended process follows a question-driven approach:
1.  **Define the High-Level Purpose:** What does the instrument do? What are its actions, telemetry data, and failure modes?
2.  **Define the Hardware Configuration:** List all pins and critical operational parameters.
3.  **Define the Command Interface:** Specify the `func`, `args`, and success/failure conditions for each command the instrument accepts.
4.  **Define the States:** For each custom state, describe its purpose, entry/exit actions, and transition logic.

Please refer to **`docs/socratic_design_guidelines.md`** for a complete walkthrough and a template for creating your instrument's design specification.

## Contributing

Contributions are welcome! If you'd like to improve the framework or add a new instrument, please feel free to fork the repository and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
```

### deploy_firmware.bat

```
@echo off
:: ============================================================================
:: Deploys firmware and libraries to a CircuitPython microcontroller.
::
:: USAGE:
::   deploy_firmware.bat <DRIVE_LETTER>
::
:: EXAMPLE:
::   deploy_firmware.bat G
::
:: WHAT IT DOES:
::   1. Checks if a drive letter was provided.
::   2. Checks if the target drive exists.
::   3. Creates a 'lib' directory on the drive if it doesn't exist.
::   4. Deletes the old 'firmware', 'communicate', and 'shared_lib'
::      directories from the drive's 'lib' folder. This is crucial
::      to remove any old or deleted files.
::   5. Copies the new versions of these directories from the project
::      folder to the drive's 'lib' folder.
:: ============================================================================

set "DRIVE_LETTER=%~1"

:: --- Input Validation ---
if "%DRIVE_LETTER%"=="" (
    echo.
    echo ERROR: No drive letter provided.
    echo.
    echo USAGE: %~n0 G
    echo.
    goto :end
)

if not exist %DRIVE_LETTER%:\ (
    echo.
    echo ERROR: Drive %DRIVE_LETTER%: does not exist.
    echo Please check the drive letter and try again.
    echo.
    goto :end
)

:: --- Set up paths ---
set "DEST_DRIVE=%DRIVE_LETTER%:"
set "DEST_LIB_PATH=%DEST_DRIVE%\lib"

echo.
echo ======================================================================
echo  Deploying to CircuitPython Device on Drive %DEST_DRIVE%
echo ======================================================================
echo.

:: Create the 'lib' directory if it doesn't exist
if not exist "%DEST_LIB_PATH%" (
    echo Creating destination directory: %DEST_LIB_PATH%
    mkdir "%DEST_LIB_PATH%"
)

:: --- List of directories to copy ---
set "DIRS_TO_COPY=firmware communicate shared_lib"

:: --- Main Deployment Loop ---
for %%d in (%DIRS_TO_COPY%) do (
    echo.
    echo --- Processing %%d ---
    
    REM First, remove the old directory from the device to ensure a clean copy
    if exist "%DEST_LIB_PATH%\%%d\" (
        echo  - Removing old version of %%d from device...
        rd /s /q "%DEST_LIB_PATH%\%%d"
    ) else (
        echo  - No old version of %%d found on device.
    )

    REM Now, copy the new directory from the project source
    if exist "%%d\" (
        echo  - Copying new version of %%d to device...
        xcopy "%%d" "%DEST_LIB_PATH%\%%d\" /E /I /Y /Q /C
    ) else (
        echo  - WARNING: Source directory %%d not found in project folder.
    )
)

echo.
echo ======================================================================
echo  Deployment complete!
echo ======================================================================
echo.

:end
pause
```

### requirements.txt

```
adafruit-board-toolkit
pyserial

```

### run_fake_device_test.py

```python
import time
import json
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message

# This utility requires the adafruit-board-toolkit, which should be in requirements.txt
try:
    from adafruit_board_toolkit.circuitpython_serial import data_comports
except ImportError:
    print("Error: 'adafruit-board-toolkit' is not installed.")
    print("Please run 'pip install adafruit-board-toolkit'")
    exit()

def find_device_port():
    """Scans for and returns the first available CircuitPython data port."""
    ports = data_comports()
    if not ports:
        return None
    return ports[0].device

def main():
    """Main function to run the live test against the fake SDL device."""
    print("--- SDL Host Live Test ---")
    
    # 1. Find the connected CircuitPython device
    device_port = find_device_port()
    if not device_port:
        print("\nERROR: No CircuitPython device found. Make sure it is connected.")
        return

    print(f"\nFound device at: {device_port}")

    # 2. Set up the communication channel (Postman)
    # The timeout=0.1 makes the receive() call non-blocking
    postman_params = {"port": device_port, "baudrate": 115200, "timeout": 0.1, "protocol": "serial"}
    postman = SerialPostman(postman_params)
    
    try:
        postman.open_channel()
        print("Serial port opened successfully. Listening for messages...")
        print("Press Ctrl+C to exit.")

        last_blink_time = 0
        blink_interval = 10  # Send a blink command every 10 seconds

        # 3. Enter the main communication loop
        while True:
            # --- Check for incoming messages from the device ---
            raw_message_from_device = postman.receive()
            if raw_message_from_device:
                try:
                    # Attempt to parse the JSON string into a Message object
                    message = Message.from_json(raw_message_from_device)
                    print(f"\nRECEIVED <-- [{message.status}] {message.to_dict()}")
                except (json.JSONDecodeError, ValueError):
                    # If parsing fails, just print the raw data
                    print(f"\nRECEIVED RAW <-- {raw_message_from_device}")

            # --- Send a command periodically ---
            if time.time() - last_blink_time > blink_interval:
                print("\nSending blink command...")
                
                # Create the blink instruction message
                blink_payload = {"func": "blink", "args": ["3"]}
                blink_message = Message.create_message(
                    subsystem_name="HOST",
                    status="INSTRUCTION",
                    payload=blink_payload
                )

                # Send the serialized message to the device
                postman.send(blink_message.serialize())
                print(f"SENT --> [INSTRUCTION] {blink_message.to_dict()}")
                
                last_blink_time = time.time()

            # A short sleep to prevent the loop from using 100% CPU
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nExiting program.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # Ensure the serial port is closed on exit
        if postman.is_open:
            postman.close_channel()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
```

## communicate

### __init__.py

```python

```

### circuitpython_postman.py

```python
# communicate/circuitpython_postman.py
#type: ignore
import usb_cdc  # Make sure this is not commented out
from .postman import Postman

class CircuitPythonPostman(Postman):
    """
    Postman implementation for serial communication using data line in CircuitPython.
    usb_cdc.enable(console=True, data=True) belongs in boot.py
    """

    def _open_channel(self):
        """Opens the serial port."""
        return usb_cdc.data

    def _close_channel(self):
        """Closes the serial port."""
        # Nothing to do here

    def _send(self, value):
        """Sends data over the serial port."""
        message = str(value)
        if not message.endswith('\n'):
            message += '\n'
        # Assuming you want to send a string, encode it to bytes
        data = message.encode('utf-8')  # Ensure the data is encoded as bytes
        self.channel.write(data)

    def _receive(self):
        """
        Receives data from the serial port in a NON-BLOCKING way.
        """
        # --- FIX IS HERE ---
        # First, check if there is any data waiting to be read.
        if self.channel.in_waiting > 0:
            # If there is data, read one line.
            data = self.channel.readline()
            # Decode the bytes to a string, stripping any trailing whitespace.
            return data.decode('utf-8').strip()
        
        # If no data is waiting, return an empty string immediately.
        # This prevents the main loop from blocking.
        return ""
```

### host_utilities.py

```python
# type: ignore
"""
Utility functions relevant to the host (PC/MAC/LINUX) computer operating the software driven laboratory

Author(s): BoB LeSuer
"""
from shared_lib.utility import check_if_microcontroller

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

```

### postman.py

```python
#type: ignore

class Postman():
    """
    Base class for message transmission between devices.
    """

    def __init__(self, params: dict):
        """
        Initializes the Postman with a dictionary of parameters.

        Args:
            params: A dictionary containing the configuration parameters.
                   Required Keys: "protocol" (e.g., "serial", "rest", "mqtt")
                   Optional Keys (depending on protocol):
                       "port" (for serial)
                       "baudrate" (for serial, default 115200)
                       "timeout" (for serial, default 1)
                       "url" (for REST)
                       "topic" (for MQTT)
                       ... (other protocol-specific parameters)
        """
        self.params = params
        self.protocol = params.get("protocol")
        if not self.protocol:
            raise ValueError("Protocol must be specified in params")

        self.channel = None
        self.is_open = False

    def open_channel(self):
        """
        Opens the communication channel (implementation-specific).
        """
        if self.is_open:
            return  # Do nothing if already open.  Raise exception?

        self.channel = self._open_channel()
        self.is_open = True

    def close_channel(self):
        """
        Closes the communication channel (implementation-specific).
        """
        if not self.is_open:
            return  # Do nothing if already closed. Raise exception?

        self._close_channel()
        self.channel = None
        self.is_open = False

    def send(self, value):
        """
        Sends a message (implementation-specific).
        """
        if not self.is_open:
            raise ValueError("Channel is not open.  Must call open_channel() first.")
        self._send(value)

    def receive(self):
        """
        Receives a message (implementation-specific).
        """
        if not self.is_open:
            raise ValueError("Channel is not open.  Must call open_channel() first.")
        return self._receive()

    # Implementation specific

    def _open_channel(self):
        """implementation to open channel"""
        raise NotImplementedError("Implementation specific open not implemented")

    def _close_channel(self):
        """implementation to close channel"""
        raise NotImplementedError("Implementation specific close not implemented")

    def _send(self, value):
        """implementation to send"""
        raise NotImplementedError("Implementation specific send not implemented")

    def _receive(self):
        """implementation to receive"""
        raise NotImplementedError("Implementation specific receive not implemented")
    
#type: ignore

class DummyPostman(Postman):
    """
    Dummy Postman for testing without a real communication channel.  Can be configured
    to send canned responses.
    """

    def __init__(self, params: dict = None, canned_responses=None):
        """
        Initializes the DummyPostman.

        Args:
            params: Dictionary of parameters (ignored, present for compatibility).
            canned_responses: An optional list of values to be returned by 
                              successive calls to receive().  If None, receive() 
                              will always return an empty string.  If a list,
                              receive() will return values from the list in 
                              order, then empty strings once the list is exhausted.
        """
        super().__init__(params or {})  # Pass empty dict if params is None
        self.canned_responses = canned_responses or []
        self.response_index = 0
        self.sent_values = []  # Store sent values for verification

    def _open_channel(self):
        """Dummy open - does nothing."""
        pass  # No real channel to open

    def _close_channel(self):
        """Dummy close - does nothing."""
        pass  # No real channel to close

    def _send(self, value):
        """Stores the sent value for later retrieval."""
        self.sent_values.append(value)

    def _receive(self):
        """Returns a canned response or an empty string."""
        if self.response_index < len(self.canned_responses):
            response = self.canned_responses[self.response_index]
            self.response_index += 1
            return response
        else:
            return ""

    def get_sent_values(self):
        """Returns a list of all values sent."""
        return self.sent_values

    def clear_sent_values(self):
        """Clears the list of sent values."""
        self.sent_values = []
```

### secretary.py

```python
import time
from shared_lib.statemachine import StateMachine, State

'''
The secretary may need better task management. Right now it is very linear. Perhaps in a refactor reading a new message starts
with setting flags for what to do with the message (route, mail, file). Then there is a new state processing which cycles
through the other states. I cannot envision a situation when we need to go through secretary states more than once for a given
message. State machine might already be overkill.

For now: Monitor watches the inbox/outbox. If outbox gets populated, call the postman. If inbox is not empty, read. Reading
involves routing or mailing (not states, but probably will be in the future) and filing (a state). All of these should go back
reading because the message is processed multiple times. A flag of some sort informs secretary that everyone is done with the 
message, at which point it is removed from memory and we go back to monitoring.
'''


# Assuming you have MessageBuffer, Postman, and other relevant classes
class SecretaryStateMachine(StateMachine):
    """
    A state machine to manage message processing and routing.
    """

    def __init__(self, inbox, outbox, subsystem_router, filer=None, postman = None, name = "secretary"):
        """Initializes the SecretaryStateMachine."""
        super().__init__(init_state='Monitoring', name=name)  # set the name for the logging

        self.inbox = inbox
        self.outbox = outbox
        self.subsystem_router = subsystem_router
        self.filer = filer
        self.postman = postman
        #Add states
        self.add_state(Monitoring())
        self.add_state(Reading())
        self.add_state(Filing())
        self.add_state(Error())

class Monitoring(State):
    """
    Secretary state of monitoring the inbox and outbox.
    If either one is populated, do something about it.
    Prefers sending messages
    """
    @property
    def name(self):
        return 'Monitoring'
    
    def enter(self, machine):
        machine.log.info("Monitoring for new tasks.")

    def update(self, machine):
        """
        Checks outbox and calls postman if necessary. Then checks the inbox 
        for new messages and transitions to ProcessMessage.
        """
        if not machine.outbox.is_empty():
            machine.log.info("Message in outbox. Calling the postman to send.")
            mail = machine.outbox.get()
            if mail:
                # Issue 2 FIX: Serialize the message object before sending.
                machine.postman.send(mail.serialize())
        else:
            message = machine.inbox.get()
            if message:
                machine.flags["current_message"] = message #Sets the current message to be used in other functions
                machine.log.info("New message received. Transitioning to Reading.")
                machine.go_to_state('Reading')


class Reading(State):
    """
    Secretary state of reading a message from the inbox and deciding what to do
    Upon entering, create flags to decide if message should be filed, routed, or mailed. 
    Then, only exit state if all three are false.
    """
    @property
    def name(self):
        return 'Reading'

    def enter(self, machine):
        message = machine.flags.get("current_message")
        if message:
            # Log the dictionary representation for better readability
            machine.log.debug(f"Now reading message: {message.to_dict()}")
        else: 
            machine.log.warning("Entered Reading state with no message! Returning to Monitoring.")
            machine.go_to_state('Monitoring')


    def update(self, machine):
        # Issue 1 FIX: Get the message from the machine flags, not the inbox.
        message = machine.flags.get("current_message")

        if not message:
             # If there's no message, we shouldn't be here. Go back to monitoring.
             machine.log.warning("No message found in flags during Reading update. Returning to Monitoring.")
             machine.go_to_state('Monitoring')
             return # Exit the update function for this cycle

        # Determine actions to take based on the message object's properties
        if self.should_route_to_subsystem(message, machine):
            machine.log.debug(f"Routing message payload: {message.payload}")
            machine.subsystem_router.route(message)

        if self.should_send_to_outbox(message, machine):
            machine.log.debug(f"Mailing message payload: {message.payload}")
            machine.outbox.store(message)

        if self.should_file_message(message, machine):
            machine.log.debug(f"Filing message payload: {message.payload}")
            machine.go_to_state("Filing")
        else:
            # If not filing, the message is processed, so clear the flag and go back to monitoring.
            machine.flags["current_message"] = None
            machine.go_to_state("Monitoring")


    def should_file_message(self, message, machine):
      # Always file messages - if you don't want the messages, use the CircularFiler with 'print':False
      return True
    
    def should_route_to_subsystem(self, message, machine):
      # Route any message with the status "INSTRUCTION"
      machine.log.debug(f"Checking if message status '{message.status}' should be routed...")
      return message.status == "INSTRUCTION"
    
    def should_send_to_outbox(self, message, machine):
      # This logic is for the host-side secretary to echo things.
      # Responses should be generated by the subsystem router, so this is correctly False.
      return False



class Filing(State):
    """Filing class reads the message and processes the message to complete the goal of the subsystem"""
    @property
    def name(self):
        return 'Filing'

    def enter(self, machine):
        machine.log.info("Entering Filing state.")

    def update(self, machine):
        # Issue 1 FIX: Get the message from machine flags.
        message = machine.flags.get("current_message")
        if not message:
            machine.log.warning("No message in flags to file. Returning to Monitoring.")
            machine.go_to_state('Monitoring')
            return

        if machine.filer:
            machine.filer.file_message(message)
            machine.log.info("Message filed.")
        else:
            machine.log.warning("No filing system configured to store the message.")
        
        # After filing, we're done with this message. Clear the flag and go back to monitoring.
        machine.flags["current_message"] = None
        machine.go_to_state('Monitoring')

class Error(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Error'

    def enter(self, machine):
        machine.log.critical("An error has occurred in the Secretary.")
        error_msg = machine.flags.get("error_message", "No error message provided.")
        machine.log.critical(error_msg)

    def update(self, machine):
        time.sleep(10)
        machine.log.warning("Exiting error state and returning to Monitoring.")
        machine.go_to_state("Monitoring")

'''
Secretary may always have a technician to work with, but it is possible that technicians are part of the subsystems they control.
Alternatively, this might be technician logic. 
'''
class Router: 
    def route(self, message):
        # Add code here that routes messages to the right subsytem
        pass  # Example, subsystems may be "engine", "brakes", "lights"


'''
Secretary needs a way to file messages, so this class is a part of secretary.py
'''
class Filer():
    """
    Base class for filing messages
    """

    def __init__(self, param = {}):
        """
        Initilize the filing system
        """
        self.parameters = param # Implementation specific parameter set

    def file_message(self, msg = None): 
        """
        Files message
        """
        if msg:
            self._file_message(msg) # Implementation specific filing
        else:
            pass

    def _file_message(self, msg):
        """files message, implementation specific"""
        raise NotImplementedError("Implementation specific filing not implemented")

class CircularFiler(Filer):
    """
    Prints message to console unless print parameter is False
    """

    def __init__(self, param = {'print': True}):
        super().__init__(param)
        

    def _file_message(self, msg): 
        if self.parameters['print']:
            # Print the dictionary representation of the message for readability
            print(f"Filer: {msg.to_dict()}")
        else:
            # Silently "file" the message
            pass
```

### serial_postman.py

```python
import serial
from .postman import Postman

class SerialPostman(Postman):
    """
    Postman implementation for serial communication in standard Python.
    """

    def _open_channel(self):
        """Opens the serial port."""
        try:
            port = self.params.get("port")
            baudrate = self.params.get("baudrate", 115200)  # Default baudrate
            timeout = self.params.get("timeout", 1)  # Default timeout
            ser = serial.Serial(port, baudrate, timeout=timeout)
            return ser
        except serial.SerialException as e:
            raise IOError(f"Could not open serial port {self.params.get('port')}: {e}")

    def _close_channel(self):
        """Closes the serial port."""
        self.channel.close()

    def _send(self, value):
        """Sends data over the serial port."""
        message = str(value)
        if not message.endswith('\n'):
            message += '\n'
        # Assuming you want to send a string, encode it to bytes
        data = message.encode('utf-8')  # Ensure the data is encoded as bytes
        self.channel.write(data)

    def _receive(self):
        """Receives data from the serial port."""
        # Read a line of data (terminated by newline character)
        data = self.channel.readline()
        # Decode the bytes to a string, stripping any trailing whitespace
        return data.decode('utf-8').strip()
```

## docs

### AI assistent instrument design.md

```markdown
# Future AI Prompt Template: New Instrument Firmware Generation

## Persona and Role

You are an expert firmware developer specializing in state-machine-based architectures for laboratory automation. You are intimately familiar with the provided software stack and its core design principles (unified state machine, separation of configuration from logic, centralized command handling, and use of common libraries).

## Primary Goal

Your primary goal is to draft the initial, high-quality firmware files (`__init__.py`, `states.py`, `handlers.py`) for a new instrument that will be integrated into the provided software framework. The output should be a robust and well-commented starting point for further development.

## The Process to Follow

You will follow a strict, three-step process:

**Step 1: Analyze the Provided Materials**
First, thoroughly analyze the two inputs I will provide below:
1.  **The Current Software Stack:** Internalize the existing architectural patterns, the structure of the `StateMachine` class, the function of common libraries (`common_states`, `command_library`), and how existing instruments are assembled.
2.  **The New Instrument Design Spec Sheet:** Carefully review the user-provided specifications for the new instrument. Understand its purpose, hardware, commands, and states.

**Step 2: Ask Clarifying Questions (Critical Step)**
This is the most important step. Before writing any code, identify any ambiguities, potential design conflicts, missing information, or architectural decisions that need to be made based on the spec sheet. Formulate a series of clear, numbered questions for me (the user) to answer.

Your questions should be designed to solidify the instrument's logic, focusing on areas such as:
*   **State Transition Logic:** "In the `Homing` state, what is the exact physical sequence of motor movements and endstop checks?"
*   **Command Behavior:** "For the `dispense` command, if the requested volume is not a multiple of the pump's increment, what is the desired rounding behavior (reject, round up, or round down)?"
*   **Hardware Assumptions:** "The spec sheet mentions a user button. What action should this button trigger in the `Idle` state versus the `Dispensing` state?"
*   **Complex Workflows:** "The `calibrate` command seems to involve multiple steps. Can you describe the ideal user story for how this interactive process should work?"

**Do not proceed to Step 3 until I have provided answers to your questions.**

**Step 3: Draft the Firmware Files**
Once I have provided answers to your clarifying questions, generate the first draft of the three core firmware files: `__init__.py`, `states.py`, and `handlers.py`.

The draft must adhere to the following quality standards:
*   **Heavily Commented:** Explain the purpose of key blocks of code, especially where it relates to the spec sheet and my clarifying answers.
*   **Architecturally Sound:** Adhere strictly to the existing patterns of the framework (e.g., using the `CONFIG` dictionary, placing guards in handlers, using the state sequencer pattern if necessary).
*   **Includes Placeholders:** For complex, domain-specific logic that cannot be fully implemented without real-world testing (like kinematics calculations or trajectory planning), create clearly marked placeholder functions or comments (e.g., `# TODO: Implement kinematics calculation here`).
*   **Functional Core:** The generated code should be syntactically correct and provide a working foundation for the instrument. Basic commands and states should be functional, even if complex parts are placeholders.

---

## User-Provided Inputs

*You will fill out these sections when using this template.*

### Input 1: Current Software Stack

`[PASTE ALL RELEVANT .py FILES FROM YOUR PROJECT HERE, INCLUDING aht20_sensor AND sidekick EXAMPLES FOR CONTEXT]. An easy way to do this is with the all-in-one.py script found [here](https://raw.githubusercontent.com/bobthechemist/codecave/master/all-in-one.py)`

### Input 2: New Instrument Design Spec Sheet

`[PASTE THE COMPLETED SPEC SHEET TEMPLATE FOR YOUR NEW INSTRUMENT HERE]. Examples of the template are provided in the documentation.`
```

### socratic_design_guidelines.md

```markdown
## Documentation: Designing a New Instrument

### 1. Our Design Philosophy

This framework is built on a state-machine-based design philosophy. This approach helps manage complexity, prevent bugs, and create responsive, non-blocking instruments. The core principles are:

*   **One Machine, One State:** Each instrument is represented by a single, unified `StateMachine` instance. At any given moment, the machine is in one, and only one, well-defined state (e.g., `Initializing`, `Idle`, `Moving`).
*   **Separation of Data and Logic:** We strictly separate the instrument's static configuration (the *data*, like pin numbers and settings) from its dynamic behavior (the *logic*, defined in states and handlers).
*   **Centralized Command Handling:** The `StateMachine` itself is responsible for managing and dispatching commands. States simply indicate *when* the machine should listen for those commands.
*   **Common, Reusable Components:** We leverage a library of common states (`GenericIdle`, `GenericError`) and command handlers (`ping`, `help`) to reduce boilerplate code and ensure consistent behavior across all instruments.

Following this design process will produce a clear "spec sheet" for your new instrument. This document serves as a blueprint that a programmer—or a capable AI—can use to draft the firmware files (`__init__.py`, `states.py`, `handlers.py`) with high accuracy.

### 2. The Design Process: A Question-Driven Approach

The best way to design a new instrument is to answer a series of questions, moving from a high-level overview down to the specific details of each state. This Socratic, question-driven method ensures all aspects of the instrument's behavior are considered.

#### Step 1: High-Level Instrument Definition

Before writing any code, answer these four core questions about the instrument as a whole:

1.  **What is the primary purpose of this instrument?** (e.g., "To measure temperature and humidity," "To move a robotic arm to specified coordinates.")
2.  **What are the primary actions it can perform?** (e.g., "Take a reading," "Move to an X,Y coordinate," "Turn a motor on.")
3.  **What data does it need to report back periodically?** (This defines your telemetry. e.g., "The current temperature," "The motor's logical position.")
4.  **What are the critical failure conditions?** (e.g., "The sensor cannot be found on the I2C bus," "An endstop is hit unexpectedly.")

#### Step 2: Defining the Hardware Configuration

All static hardware definitions and settings belong in a single `CONFIG` dictionary in the instrument's `__init__.py` file. This creates a central "dashboard" for the instrument's physical setup.

*   List every pin the microcontroller will use. Give each pin a descriptive name.
*   List any key operational parameters (e.g., motor speeds, pump timings, physical dimensions).
*   List any "safe limits" that the instrument must not violate.

#### Step 3: Defining the Command Interface

This defines the API that the host computer will use to control the instrument. For each custom command, define:

*   **Function Name (`func`):** A short, verb-based name (e.g., `read_now`, `move_to`).
*   **Description:** A clear, one-sentence description of what the command does.
*   **Arguments (`args`):** What data, if any, the host must provide.
*   **Success Condition:** What happens when the command completes successfully? (e.g., "Returns a `SUCCESS` message with the sensor data," "Transitions to the `Moving` state.")
*   **Guard Conditions:** What criteria must be met for this command to be accepted? (e.g., "The machine must be homed," "The target coordinates must be within safe limits.")

#### Step 4: Defining the States

Now, apply the Socratic method to each individual state your instrument will have. Remember, you get `GenericIdle` and `GenericError` for free, so you only need to design the states unique to your instrument.

For each custom state, answer these five questions:

1.  **Purpose:** What is this state's single, clear responsibility?
2.  **Entry Actions (`enter()`):** What needs to be set up *the moment* we enter this state? (e.g., start a timer, reset a counter, turn on a pin).
3.  **Internal Actions (`update()`):** What is the main work this state does on *every loop*? (e.g., check a timer, monitor a sensor, step a motor, listen for commands).
4.  **Exit Events & Triggers:** How does this state know its job is finished? What causes a transition to another state? (e.g., a timer expires, a task is complete, an error is detected, an `abort` command is received).
5.  **Exit Actions (`exit()`):** What cleanup is required when leaving this state to ensure the hardware is safe? (e.g., turn off a motor, reset a flag).

### 3. The Design Document Template

Copy the following Markdown template into a new file and fill it out for your new instrument. This completed document is the final "spec sheet."

---

## Instrument Design: AHT20 Environmental Sensor

### 1. Instrument Overview

*   **Primary Purpose:** To measure and report ambient temperature and relative humidity.
*   **Primary Actions:** Initialize the sensor, periodically read sensor values, and perform a manual read on command.
*   **Periodic Telemetry Data:** The current temperature (in Celsius) and relative humidity (in %).
*   **Critical Failure Conditions:** The AHT20 sensor is not detected on the I2C bus during initialization.

### 2. Hardware Configuration (`CONFIG` dictionary)

*(Note: The AHT20 uses the board's default I2C pins, so we don't need to define them explicitly in this simple case.)*
```python
AHT20_CONFIG = {
    # No custom pin definitions needed for this simple sensor.
    # A more complex device would list all pins here.
}
```

### 3. Command Interface

| `func` Name | Description | Arguments | Success Condition | Guard Conditions |
| :--- | :--- | :--- | :--- | :--- |
| `read_now` | Immediately reads the sensor and returns the values. | None | Returns a `SUCCESS` message with a payload containing the temperature and humidity. | None. |

### 4. State Definitions

#### State: `Initialize`
1.  **Purpose:** To connect to the AHT20 sensor via the I2C bus.
2.  **Entry Actions (`enter()`):**
    *   Attempt to create an `I2C` object for the board.
    *   Attempt to instantiate the `adafruit_ahtx0.AHTx0` sensor object using the I2C bus.
    *   Attach the sensor object to the `machine` instance (e.g., `machine.sensor`).
3.  **Internal Actions (`update()`):** None. This state should transition immediately.
4.  **Exit Events & Triggers:**
    *   **On Success:** The sensor is instantiated without error. Trigger: Transition to `Idle`.
    *   **On Failure:** An exception is raised (e.g., `ValueError` if the sensor is not found). Trigger: Set an `error_message` flag and transition to `Error`.
5.  **Exit Actions (`exit()`):** None.


```

### socratic_sidekick.md

```markdown
# Instrument design: Sidekick liquid dispenser (sidekick)

## 1. Instrument Overview

* Primary purpose: to dispense liquid from four displacement pumps with 2 dimensional resolution
* primary actions: move dispensing effector, dispense liquids
* periodic telemetry data: current end effector position
* critical failure conditions: endstops triggered (when not expected)

## 2. Hardware configuration

``` python
SIDEKICK_CONFIG = {
    "pins": {
        # --- Motor 1 (Top Motor) ---
        "motor1_step": board.GP1,
        "motor1_dir": board.GP0,
        "motor1_enable": board.GP7,  # Was 'motor1_sleep'

        # --- Motor 2 (Bottom Motor) ---
        "motor2_step": board.GP10,
        "motor2_dir": board.GP9,
        "motor2_enable": board.GP16, # Was 'motor2_sleep'
        
        # NOTE: Microstepping pins are recorded here for completeness.
        # Simple drivers use these, but advanced drivers (TMC) use UART/SPI.
        # This framework can be extended later to use them if needed.
        "motor1_m0": board.GP6,
        "motor1_m1": board.GP5,
        "motor2_m0": board.GP15,
        "motor2_m1": board.GP14,

        # --- Endstops ---
        # The old code referred to them by location ('front'/'rear').
        # Tying them to the motor they home is more robust.
        "endstop_m1": board.GP18, # Was 'lsfront'
        "endstop_m2": board.GP19, # Was 'lsrear'

        # --- User Button ---
        "user_button": board.GP20, # Was 'purgebutton'

        # --- Pumps ---
        "pump1": board.GP27,
        "pump2": board.GP26,
        "pump3": board.GP22,
        "pump4": board.GP21,
    },
    
    "motor_settings": {
        # Your code mentions both 1.8 and 0.9 degree motors, but the
        # stepsize calculation (0.1125) points to 1/8 microstepping
        # on a 0.9 degree motor. (0.9 degrees / 8 microsteps).
        "step_angle_degrees": 0.9,
        "microsteps": 8,
        # Calculated from stepdelay = 0.0010. A full step cycle is two delays.
        # 1 / (2 * 0.0010) = 500 steps per second.
        "max_speed_sps": 500,
    },

    "pump_timings": {
        # Extracted from the dispense() function's time.sleep() calls.
        "aspirate_time": 0.1, # seconds
        "dispense_time": 0.1, # seconds
    },

    "kinematics": {
        # These are the physical dimensions of the SCARA arm segments.
        # They come from the __init__ arguments: L1, L2, L3, Ln
        "L1": 7.0,
        "L2": 3.0,
        "L3": 10.0,
        "Ln": 0.5,
    },

    "safe_limits": {
        # These will need to be determined experimentally after homing,
        # but we can create placeholders. These are in logical motor steps.
        "m1_min_steps": 0,
        "m1_max_steps": 10000, # Example value
        "m2_min_steps": 0,
        "m2_max_steps": 10000, # Example value
    }
}
```
## 3. Command interface

- home
    - description: returns effector to home position
    - arguments: None
    - success condition: Returns a `SUCCESS` message
    - guard conditions: None
- move_to
    - description: moves the effector to a position
    - arguments: (x,y)
    - success condition: Returns a `SUCCESS` message with current position
    - guard condition: validate the (x,y) argument passed is a legitimate position
- move
    - description moves the effector relative to its current position
    - arguments: (dx, dy)
    - success condition: Returns a `SUCCESS` message with current position
    - guard condition: ensure current position + (dx,dy) results in a legitimate position
- calibrate
    - description: calibrates the positioning of the end effector
    - arguments: None
    - success condition: Returns a `SUCCESS` message with calibration information, stores calibration data.
    - guard condition: motors need to be homed. 
    - special note: The move command will move to the center of the end effector. Calibrate will need to know or determine the offset between this point and each of the four dispensing tubes.
- dispense
    - description: dispenses liquid from 1 of four pumps
    - arguments: (which_pump, volume)
    - success condition: Returns a `SUCCESS` message with amount of liquid dispensed and the pump from which it was dispensed.
    - guard condition: valid parameters provided. Volumes can only be dispensed in fixed increments (typically 10 microliters)
- dispense_at
    - description: perform a move and dispense liquid from 1 of four pumps
    - arguments: (which_pump, volume, x, y)
    - success condition: Returns `SUCCESS` message with amount of liquid dispensed and the pump from which it was dispensed.
    - guard condition: valid parameters provided

## 4. States

- Initialize
    - purpose: assign and enable microcontroller pins for the motors, pumps, and switches
    - entry actions: assign pins according to the configuration file
    - internal actions: none
    - exit events:
        - success: no errors raised. Trigger transition to Idle
        - failure: an exception is raised. Trigger error message and transition to Error
    - exit actions: ensure all motors and pumps are off
- Homing
    - purpose: determine the limits of the 2 motors controling the robot arm
    - entry action: user command issued or possibly from a state that requires homing
    - internal actions: determine how far the motors can travel before triggering the endstop and assigning this point as zero. Do this for both motors
    - exit events: 
        - success: no errors raised. Trigger transition to Idle
        - failure: an exception is raised. Trigger error message and transition to Error
    - exit actions: homed flag needs to be set
- Calibrating
    - purpose: improve the accuracy of the x,y positioning
    - entry action: user command issued
    - internal actions: home the motors if necessary, extend motors to limits to define maximum distances, store calibration information for later retrieval, return to a default position
    - exit events: 
        - success: no errors raised. Trigger transition to Idle
        - failure: an exception is raised. Trigger error message and transition to Error
    - exit actions: `SUCCESS` message sent with calibration information, which the user will need.
- Moving
    - purpose: move the end effector to a given location
    - entry action: user command or requested by another state (e.g. Calibrating)
    - internal actions: kinematics math to handle SCARA arm coordinate to cartesian coordinate transformation, determine number of steps and direction for each motor, execute number of steps for two motors controlling the arm
    - exit events:
        - success from user command: no errors raised. Trigger transition to Idle
        - success from calibrating: no errors raised. Trigger transition to Calibrating
        - failure: an exception is raised. Trigger error message and transition to Error
    - exit actions: `SUCCESS` message sent with current location, current position flag updated
- Dispensing
    - purpose: dispense from one of the four pumps
    - entry action: user command
    - internal actions: offset the effector from its current location for the selected pump, determine number of dispenses needed for target volume, execute number of dispenses, return to original location
    - exit events:
        - success: no errors raised. Trigger transition to Idle
        - failure: an exception is raised. Trigger error message and transition to Error
    - exit actions: `SUCCESS` message sent with total volume dispensed, the location, and the pump from which liquid was dispensed



```

### socratic_sidekick_ai_revised.md

```markdown
# Instrument design: Sidekick liquid dispenser (sidekick)

## 1. Instrument Overview (Unchanged)
*   **Primary purpose:** To dispense liquid from four displacement pumps with 2-dimensional resolution.
*   **Primary actions:** Move dispensing effector, dispense liquids.
*   **Periodic telemetry data:** Current end effector position in Cartesian `(x, y)` coordinates.
*   **Critical failure conditions:** Endstops triggered unexpectedly during a move.

## 2. Hardware Configuration (`SIDEKICK_CONFIG`)


``` python
SIDEKICK_CONFIG = {
    "pins": {
        # --- Motor 1 (Top Motor) ---
        "motor1_step": board.GP1,
        "motor1_dir": board.GP0,
        "motor1_enable": board.GP7,  # Was 'motor1_sleep'

        # --- Motor 2 (Bottom Motor) ---
        "motor2_step": board.GP10,
        "motor2_dir": board.GP9,
        "motor2_enable": board.GP16, # Was 'motor2_sleep'
        
        # NOTE: Microstepping pins are recorded here for completeness.
        # Simple drivers use these, but advanced drivers (TMC) use UART/SPI.
        # This framework can be extended later to use them if needed.
        "motor1_m0": board.GP6,
        "motor1_m1": board.GP5,
        "motor2_m0": board.GP15,
        "motor2_m1": board.GP14,

        # --- Endstops ---
        # The old code referred to them by location ('front'/'rear').
        # Tying them to the motor they home is more robust.
        "endstop_m1": board.GP18, # Was 'lsfront'
        "endstop_m2": board.GP19, # Was 'lsrear'

        # --- User Button ---
        "user_button": board.GP20, # Was 'purgebutton'

        # --- Pumps ---
        "pump1": board.GP27,
        "pump2": board.GP26,
        "pump3": board.GP22,
        "pump4": board.GP21,
    },
    
    "motor_settings": {
        # Your code mentions both 1.8 and 0.9 degree motors, but the
        # stepsize calculation (0.1125) points to 1/8 microstepping
        # on a 0.9 degree motor. (0.9 degrees / 8 microsteps).
        "step_angle_degrees": 0.9,
        "microsteps": 8,
        # Calculated from stepdelay = 0.0010. A full step cycle is two delays.
        # 1 / (2 * 0.0010) = 500 steps per second.
        "max_speed_sps": 500,
    },

    "pump_timings": {
        # Extracted from the dispense() function's time.sleep() calls.
        "aspirate_time": 0.1, # seconds
        "dispense_time": 0.1, # seconds
    },

    "kinematics": {
        # These are the physical dimensions of the SCARA arm segments.
        # They come from the __init__ arguments: L1, L2, L3, Ln
        "L1": 7.0,
        "L2": 3.0,
        "L3": 10.0,
        "Ln": 0.5,
    },

    "safe_limits": {
        # These will need to be determined experimentally after homing,
        # but we can create placeholders. These are in logical motor steps.
        "m1_min_steps": 0,
        "m1_max_steps": 10000, # Example value
        "m2_min_steps": 0,
        "m2_max_steps": 10000, # Example value
    },
    # --- NEW: Added based on your feedback ---
    "home_position": {
        # A safe "parking" spot in Cartesian (x, y) coordinates.
        # If set to None, the home command will use the motor-zero position.
        "x": 10.0, # cm
        "y": 5.0   # cm
    },
    "pump_offsets": {
        # The (dx, dy) offset in cm from the arm's center point for each pump.
        "p1": {"dx": 0.5, "dy": 0.0},
        "p2": {"dx": 0.0, "dy": 0.5},
        "p3": {"dx": -0.5, "dy": 0.0},
        "p4": {"dx": 0.0, "dy": -0.5},
    }
}
```

## 3. Command Interface 

| `func` Name | Description | Arguments | Success Condition | Guard Conditions |
| :--- | :--- | :--- | :--- | :--- |
| `home` | Finds the zero position using endstops, then moves to the pre-defined safe parking spot. | None | Returns a `SUCCESS` message when complete. | None. |
| `move_to` | Moves the arm's center point to an **absolute** `(x, y)` Cartesian coordinate. | `{"x": float, "y": float}` | Returns a `SUCCESS` message with the final position. | Must be homed. Coordinates must be within safe travel limits. |
| `move_rel` | Moves the arm relative to its **current** position by `(dx, dy)`. | `{"dx": float, "dy": float}` | Returns a `SUCCESS` message with the final position. | Must be homed. Target coordinates must be within safe travel limits. |
| `dispense` | Dispenses from a specified pump **at the current location**. Involves a small offset move for the pump. | `{"pump": str, "vol": float}` | Returns a `SUCCESS` message. | Must be homed. `pump` must be valid. `vol` will be rounded down and a warning issued. |
| `dispense_at` | An **atomic operation** that moves the specified pump to an absolute `(x, y)` coordinate and then dispenses. | `{"pump": str, "vol": float, "x": float, "y": float}` | Returns a `SUCCESS` message. | Must be homed. All parameters must be valid. Target coordinates must be safe. |

*(Note: The `calibrate` command is no longer needed, as its functions are handled by the `Homing` state and the new `CONFIG` entries.)*

## 4. State Definitions 

*   **`Initialize`:**
    *   **Purpose:** To configure all hardware objects based on `machine.config`.
    *   **Exit Events:** On success, transitions to `Homing`. On failure, transitions to `Error`.
    *   **Exit Actions:** On failure, ensure motors are disabled.

*   **`Homing`:**
    *   **Purpose:** To establish the arm's absolute zero position and determine the maximum travel limits.
    *   **Entry Actions:** Begins moving Motor 1 towards its endstop.
    *   **Internal Actions:**
        1.  When Motor 1 endstop is hit, set its logical position to `0`. Begin moving Motor 1 in the opposite direction to find the maximum travel distance.
        2.  Repeat the process for Motor 2.
        3.  Store the discovered travel limits in `machine.flags`.
    *   **Exit Events:**
        *   **Success:** Both motors are homed and limits are found. Set `is_homed = True` and trigger transition to `Idle`.
        *   **Failure:** An endstop is not found within a maximum number of steps (timeout). Trigger transition to `Error`.

*   **`Moving`:** (The "Motion Engine")
    *   **Purpose:** To execute a planned move from a start point to a target point. It is a generic state that does not know the reason for the move.
    *   **Entry Actions:** Reads `target_x/y` from flags, calculates the motor trajectory (steps, directions).
    *   **Internal Actions:** Pulses stepper motors according to the trajectory. Continuously checks for unexpected endstop triggers.
    *   **Exit Events:**
        *   **Success:** Target coordinates are reached. **It then checks the `machine.flags['on_move_complete']` flag.**
            *   If the flag is `'Dispensing'`, it transitions to the `Dispensing` state.
            *   Otherwise, it transitions to the default `Idle` state.
        *   **Failure:** An unexpected endstop is triggered. Set `is_homed = False` and trigger transition to `Error`.
    *   **Exit Actions:** Clear the `on_move_complete` flag to ensure it doesn't affect the next move.

*   **`Dispensing`:**
    *   **Purpose:** To execute the timed pulse sequence for one or more pumps. **This state does not perform any arm movement.**
    *   **Entry Actions:** Reads dispense parameters (`pump`, `cycles`) from flags. Initializes timers for the pump sequence.
    *   **Internal Actions:** Runs the non-blocking aspirate/dispense timing loop for all active pumps.
    *   **Exit Events:**
        *   **Success:** All requested dispense cycles are complete. Trigger transition to `Idle`.
    *   **Exit Actions:** Sends a `SUCCESS` message to the host.



```

### your_first_machine.md

```markdown
## Guide: Creating New Firmware for a Self-Driven Laboratory Instrument

### 1. Introduction

This guide will walk you through the process of creating firmware for a new instrument to integrate into the self-driven laboratory framework. Our goal is to create a complete, functional firmware package that can be controlled and monitored by the host application.

**Our Example Project: The AHT20 Environmental Sensor**

We will build firmware for a microcontroller connected to an Adafruit AHT20 Temperature and Humidity sensor. This is a great example as it involves:
*   Initializing a specific piece of hardware (the sensor).
*   Periodically reading data (temperature and humidity).
*   Sending this data back to the host as telemetry.
*   Responding to custom commands (e.g., "read the sensor right now").

**Prerequisites:**
*   A CircuitPython-compatible microcontroller.
*   An AHT20 sensor wired to the microcontroller's I2C pins.
*   The project code for the self-driven laboratory framework.
*   The necessary CircuitPython library for the AHT20 sensor. You must copy the `adafruit_ahtx0.mpy` file to the `lib` folder on your microcontroller's `CIRCUITPY` drive.

### 2. Step 1: Create the Firmware Directory

All firmware for a specific instrument lives in its own dedicated folder.

1.  Navigate to the `firmware/` directory in your project.
2.  Create a new folder. For our example, we'll name it `aht20_sensor`.
3.  Inside `aht20_sensor/`, create three empty Python files:
    *   `__init__.py`: This will be the master "assembly" file for the machine.
    *   `states.py`: This will define the unique behaviors of our sensor.
    *   `handlers.py`: This will define the logic for custom commands.

Your new directory structure will look like this:
```
firmware/
└── aht20_sensor/
    ├── __init__.py
    ├── handlers.py
    └── states.py
```

### 3. Step 2: Configure `boot.py` for the New Device

The `boot.py` file identifies your device to the host computer. Each *type* of device should have a unique Vendor ID (VID) and Product ID (PID).

1.  Open `firmware/common/boot.py`.
2.  Assign a new, unique VID/PID pair. Let's use `101` for our sensor PID and VID
3.  We haven't come up with a standard for VIDs and PIDs yet, VID 808 is reserved for Brockport Original Builds and 101 is reserved for in-lab testing. 

```python
# firmware/common/boot.py
supervisor.set_usb_identification(
    vid=101, # --> New, unique Vendor ID
    pid=101, # --> New, unique Product ID
)

usb_cdc.enable(console=True, data=True)
```
**Important:** Changes to `boot.py` only take effect after a full power cycle of the microcontroller (unplugging and plugging it back in).

### 4. Step 3: Writing the Firmware Logic

Now we will write the code for the three files we created.

#### The `states.py` File: Defining Unique Behaviors

This file contains `State` classes that are unique to this instrument. For most devices, the only required custom state is `Initialize`, as every piece of hardware has a different setup procedure.

*   **What you get from `common`:** `GenericIdle` and `GenericError`. You do not need to write these.
*   **What you must write:** `Initialize` and any other custom active states (like `Blinking` for the fake device).

**File: `firmware/aht20_sensor/states.py`**
```python
# firmware/aht20_sensor/states.py
#type: ignore
import board
from shared_lib.statemachine import State
# The sensor-specific library you copied to the device's lib folder
import adafruit_ahtx0

class Initialize(State):
    """
    Initializes the I2C bus and the AHT20 sensor. This state is custom
    because every instrument has a unique hardware setup.
    """
    @property
    def name(self):
        return 'Initialize'

    def enter(self, machine):
        super().enter(machine)
        try:
            # Create the I2C bus object.
            i2c = board.I2C()  # uses board.SCL and board.SDA
            # Create the sensor object and attach it to the machine instance.
            machine.sensor = adafruit_ahtx0.AHTx0(i2c)
            machine.log.info("AHT20 sensor initialized successfully.")
            # Once initialization is successful, transition to Idle.
            machine.go_to_state('Idle')
        except Exception as e:
            # If the sensor is not found or another error occurs, go to the Error state.
            machine.flags['error_message'] = str(e)
            machine.log.critical(f"Initialization of AHT20 failed: {e}")
            machine.go_to_state('Error')
```

#### The `handlers.py` File: Defining Custom Commands

This file contains the functions that execute your device's custom commands.

*   **What you get from `common`:** Handlers for `ping` and `help`. You do not need to write these.
*   **What you must write:** A handler function for every custom command your device supports.

Let's create a `read_now` command that immediately takes a sensor reading and sends it back.

**File: `firmware/aht20_sensor/handlers.py`**
```python
# firmware/aht20_sensor/handlers.py
#type: ignore
from shared_lib.messages import Message

def handle_read_now(machine, payload):
    """
    Handles the device-specific 'read_now' command. This is an example of
    a command that doesn't change state, but returns data directly.
    """
    try:
        temp = machine.sensor.temperature
        humidity = machine.sensor.relative_humidity
        machine.log.info(f"Manual read: Temp={temp:.2f}C, Humidity={humidity:.2f}%")
        
        # Send the data back in a SUCCESS message payload.
        response = Message.create_message(
            subsystem_name=machine.name,
            status="SUCCESS",
            payload={
                "temperature": temp,
                "humidity": humidity
            }
        )
        machine.postman.send(response.serialize())
    except Exception as e:
        machine.log.error(f"Failed to perform manual read: {e}")
        response = Message.create_message(
            subsystem_name=machine.name,
            status="PROBLEM",
            payload={"error": str(e)}
        )
        machine.postman.send(response.serialize())
```

#### The `__init__.py` File: Assembling the Machine

This is the blueprint for your machine. It imports all the pieces (states, handlers, libraries) and assembles them into the final `machine` object.

**File: `firmware/aht20_sensor/__init__.py`**
```python
# firmware/aht20_sensor/__init__.py
#type: ignore
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from our common firmware library
from firmware.common.common_states import GenericIdle, GenericError
from firmware.common.command_library import register_common_commands

# Import the device-specific parts we just wrote
from . import states
from .handlers import handle_read_now

# This is our custom telemetry callback function.
# Its purpose is to define WHAT data to send periodically.
def send_aht20_telemetry(machine):
    """Callback function to generate and send the AHT20's telemetry."""
    temp = machine.sensor.temperature
    humidity = machine.sensor.relative_humidity
    machine.log.debug(f"Telemetry: Temp={temp:.2f}C, Humidity={humidity:.2f}%")
    
    telemetry_message = Message.create_message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={
            "temperature": temp,
            "humidity": humidity
        }
    )
    machine.postman.send(telemetry_message.serialize())

# 1. Create the state machine instance
machine = StateMachine(init_state='Initialize', name='AHT20_SENSOR')

# 2. Attach the communication channel (Postman)
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the states the machine can be in
machine.add_state(states.Initialize()) # Our custom state
machine.add_state(GenericIdle(telemetry_callback=send_aht20_telemetry)) # The common idle state
machine.add_state(GenericError()) # The common error state

# 4. Define the machine's command interface
register_common_commands(machine) # Adds 'ping' and 'help'
machine.add_command("read_now", handle_read_now, {
    "description": "Immediately reads the sensor and returns the values.",
    "args": []
})

# 5. Add machine-wide flags and settings
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 10.0) # Send telemetry every 10 seconds
```

### 5. Step 4: The Main Entrypoint (`code.py`)

The `code.py` file is the first thing your microcontroller runs. We need to tell it to import and run our new `aht20_sensor` machine.

1.  Open `firmware/common/code.py`.
2.  Change `SUBSYSTEM` to `aht20_sensor`.

```python
# firmware/common/code.py
#type: ignore
from firmware.aht20_sensor import machine # --> Point to the new machine
from time import sleep

machine.log.setLevel(10) # Set to DEBUG for testing
machine.run()
while True:
    machine.update()
    sleep(0.005)
```

### 6. Step 5: Updating the Host Application

Your firmware is now complete, but the host interface doesn't know what VID/PID `809` means. We need to add an entry to our database.

1.  Open `host_app/firmware_db.py`.
2.  Add a new entry for your device.

```python
# host_app/firmware_db.py

FIRMWARE_DATABASE = {
    808: {
        'manufacturer': 'Brockport Original Builds',
        'products': {
            808: 'Fake Device',
        }
    },
    # --- NEW ENTRY ---
    101: {
        'manufacturer': 'Your lab name here',
        'products': {
            101: 'AHT20 Environmental Sensor',
        }
    }
}
# ... (rest of file is the same) ...
```

### 7. Step 6: Deployment and Debugging

You are now ready to deploy and test your new instrument.

1.  **Deploy:** Run your `deploy_firmware.bat` script, providing the correct drive letter for your microcontroller. This will copy `firmware/` and `shared_lib/` to the device.
    ```bash
    deploy_firmware.bat G
    ```
2.  **Run Host Interface:** From your project root directory, run the host GUI.
    ```bash
    python -m host_app.gui.host_interface
    ```
3.  **Test:**
    *   Click **"Scan for Devices"**. You should see your new device appear in the dropdown: `AHT20 Environmental Sensor - COMx (VID:101, PID:101)`.
    *   Click **"Connect"**.
    *   **Observe Telemetry:** Every 10 seconds, you should see a `TELEMETRY` message appear in the log with the current temperature and humidity.
    *   **Test Common Commands:**
        *   Send a `{"func": "ping"}` command and verify you get a `pong` response.
        *   Click **"Get Commands"** (which sends `{"func": "help"}`) and verify the response lists `ping`, `help`, and your new `read_now` command.
    *   **Test Custom Command:**
        *   Enter `{"func": "read_now"}` into the payload box and click **"Send Instruction"**.
        *   You should immediately receive a `SUCCESS` message containing the sensor data.
    *   **Test Error in Command:**
        *   Enter `{"func": "foobar"}` into the payload box and click **"Send Instruction"**.
        *   You should immediately receive a `PROBLEM` message indicating that the function is unknown.

Congratulations! You have successfully created, deployed, and tested a new instrument for your self-driven laboratory. You can now follow this pattern to integrate any new hardware into the system. 
```

## firmware\common

### __init__.py

```python

```

### boot.py

```python
# type: ignore
import usb_cdc
import supervisor

# Remember changes to boot.py only go into effect upon power cycling the uC.
# (The reset button won't do it.)

supervisor.set_usb_identification(
    vid=808,
    pid=808,
    # These variables cannot be written, so they are here in case something changes in the future.
    product="something awesome",
    manufacturer="Brockport Original Builds")

usb_cdc.enable(console=True, data=True)
```

### code.py

```python
# type: ignore
# Basic setup for code.py. Replace SUBSYSTEM with the appropriate one

from firmware.SUBSYSTEM import machine
from time import sleep

# Use numerical value to avoid having to do an import
#  DEBUG:10, INFO: 20, ...
machine.log.setLevel(10)
machine.run()
while True:
    machine.update()
    sleep(0.005)

```

### command_library.py

```python
# shared_lib/command_library.py
#type: ignore
from shared_lib.messages import Message

# Helper function, not a class, to register common commands.
def register_common_commands(machine):
    """
    Inspects this module and registers all common commands
    with the provided state machine instance.
    """
    # In a real implementation, you would introspect or just explicitly define.
    # For clarity, we will be explicit here.
    
    machine.add_command("help", handle_help, {
        "description": "Returns a list of all supported commands.",
        "args": []
    })
    machine.add_command("ping", handle_ping, {
        "description": "Responds with 'pong' to check connectivity.",
        "args": []
    })

# --- Handler functions are now standalone ---
def handle_help(machine, payload):
    """Sends the machine's fully assembled list of supported commands."""
    machine.log.info("Help command received. Sending capabilities.")
    response = Message.create_message(
        subsystem_name=machine.name,
        status="SUCCESS",
        payload=machine.supported_commands # Get it directly from the machine
    )
    machine.postman.send(response.serialize())

def handle_ping(machine, payload):
    """Responds with a simple 'pong'."""
    machine.log.info("Ping received. Responding.")
    response = Message.create_message(
        subsystem_name=machine.name,
        status="SUCCESS",
        payload={"response": "pong"}
    )
    machine.postman.send(response.serialize())
```

### common_states.py

```python
# firmware/common/common_states.py
# This file contains generic, reusable states for any device.
#type: ignore
import time
from shared_lib.statemachine import State
from shared_lib.messages import Message

def listen_for_instructions(machine):
    """
    A reusable helper function that checks for and dispatches incoming
    INSTRUCTION messages. Any state can call this.
    """
    raw_message = machine.postman.receive()
    if raw_message:
        try:
            message = Message.from_json(raw_message)
            if message.status == "INSTRUCTION":
                machine.handle_instruction(message.payload)
        except Exception as e:
            machine.log.error(f"Could not process message: '{raw_message}'. Error: {e}")

class GenericIdle(State):
    """
    A generic, reusable Idle state. It handles listening for instructions
    and triggers a periodic, customizable telemetry broadcast.
    """
    @property
    def name(self):
        return 'Idle'

    def __init__(self, telemetry_callback=None):
        """
        Args:
            telemetry_callback (function, optional): A function that will be
                called to send the device's specific telemetry data.
        """
        super().__init__()
        self._telemetry_callback = telemetry_callback

    def enter(self, machine):
        super().enter(machine)
        self._telemetry_interval = machine.flags.get('telemetry_interval', 5.0)
        self._next_telemetry_time = time.monotonic() + self._telemetry_interval

    def update(self, machine):
        super().update(machine)
        
        listen_for_instructions(machine)

        # Trigger the telemetry callback at the correct interval
        if time.monotonic() >= self._next_telemetry_time:
            if self._telemetry_callback:
                self._telemetry_callback(machine)
            self._next_telemetry_time = time.monotonic() + self._telemetry_interval

class GenericError(State):
    """
    A terminal state entered on critical failure (e.g., hardware init failed).
    """
    @property
    def name(self):
        return 'Error'
    
    def enter(self, machine):
        super().enter(machine)
        error_msg = machine.flags.get('error_message', "Unknown error.")
        machine.log.critical(f"ENTERING ERROR STATE: {error_msg}")
        # Turn LED on solid to indicate a persistent error
        if hasattr(machine, 'led'):
            machine.led.value = True

    def update(self, machine):
        # Stay in this state until the device is reset
        time.sleep(10)
```

## firmware\diystirplate

### __init__.py

```python
# firmware/diystirplate/__init__.py
# # type: ignore
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman
from . import states
from firmware.common.common_states import GenericIdle, GenericError
from firmware.common.command_library import register_common_commands
from .handlers import *

# Comments beginning with --> are notes for when this file is being used as a template

# Functions that the machine needs to be aware of upon instantiation
def send_telemetry(machine):
    """Callback function to generate and send device's telemetry"""
    machine.log.debug("Sending telemetry")
    telemetry_message = Message.create_message(
        subsystem_name = machine.name,
        status = "TELEMETRY",
        payload={"value": 1}
    )
    machine.postman.send(telemetry_message.serialize())


# 1. Create the state machine instance for the subsystem
# --> update `init_state` and make sure `name` is unique
machine = StateMachine(init_state='Initialize', name='STIRPLATE')

# 2. Create and attach the communication channel (Postman)
# This postman will handle the USB CDC data connection.
# --> nothing to change here.
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the defined states to the machine
# --> update this list with the correct states for your instrument
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_telemetry))
machine.add_state(states.Stirring())
machine.add_state(GenericError())

# 4. Define the machine's command interface
register_common_commands(machine)
machine.add_command("on",handle_on, {
    "description": "Turns the stir plate on.",
    "args": None
})
machine.add_command("off", handle_off, {
    "description": "Turns the stirplate off.",
    "args": None
})

# 4. Add flags that states might use. This pre-defines them for clarity.
# --> update this list with any flags or variables that are machine-wide
machine.add_flag('error_message', '')
```

### handlers.py

```python
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
```

### states.py

```python
# firmware/diystirplate/states.py
from shared_lib.statemachine import State
from time import monotonic
import board
import digitalio
from firmware.common.common_states import listen_for_instructions

class Initialize(State):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'Initialize'

    def enter(self, machine):
        # Setup hardware
        super().enter(machine)
        try:
            machine.tachometer_pin = board.A0
            machine.pwm = digitalio.DigitalInOut(board.D10)
            machine.pwm.direction = digitalio.Direction.OUTPUT
            machine.duty_cycle = 0
            machine.period = 1
            machine.start = True
            machine.log.debug(f"{machine.name} has been Initialized")
            machine.go_to_state('Idle')
        except Exception as e:
            machine.flags['error_message'] = str(e)
            machine.log.critical(f"Initialization of {machine.name} failed: {e}")
            machine.go_to_state('Error')

class Stirring(State):
    @property
    def name(self):
        return 'Stirring'

    def enter(self, machine):
        """Called once when we start stirring."""
        super().enter(machine)
        machine.log.info(f"Entering Stirring state with duty cycle {machine.duty_cycle}")
        
        # Initialize the PWM logic
        machine.pwm.value = True
        self._toggle_time = monotonic() + (machine.duty_cycle * machine.period)

    def update(self, machine):
        """Called on every loop to run the motor AND listen for commands."""
        super().update(machine)

        # 1. ALWAYS listen for commands. This allows an 'off' command to be received.
        listen_for_instructions(machine)

        # 2. Perform the non-blocking PWM work.
        if monotonic() >= self._toggle_time:
            if machine.pwm.value: # Currently HIGH, switch to LOW
                machine.pwm.value = False
                on_time = (1 - machine.duty_cycle) * machine.period
                self._toggle_time = monotonic() + on_time
            else: # Currently LOW, switch to HIGH
                machine.pwm.value = True
                off_time = machine.duty_cycle * machine.period
                self._toggle_time = monotonic() + off_time 

```

## firmware\fake

### __init__.py

```python
# firmware/fake/__init__.py
# type: ignore
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman
from . import states
from firmware.common.common_states import GenericIdle
from firmware.common.command_library import register_common_commands
from .handlers import handle_blink

def send_fake_device_telemetry(machine):
    """Callback function to generate and send the 'fake' device's telemetry."""
    machine.log.debug("Sending telemetry.")
    analog_value = machine.analog_in.value
    telemetry_message = Message.create_message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={"analog_value": analog_value}
    )
    machine.postman.send(telemetry_message.serialize())

# 1. Create the state machine instance
machine = StateMachine(init_state='Initialize', name='FAKE')

# 2. Attach the Postman
postman = CircuitPythonPostpostman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the defined states
machine.add_state(states.Initialize())
machine.add_state(GenericIdle(telemetry_callback=send_fake_device_telemetry))
machine.add_state(states.Blinking())
machine.add_state(states.Error())

# 4. DEFINE THE MACHINE'S COMMAND INTERFACE
register_common_commands(machine)
machine.add_command("blink", handle_blink, {
    "description": "Blinks the onboard LED.",
    "args": ["count (integer, default: 1)"]
})

# 5. Add flags
machine.add_flag('blink_count', 0)
machine.add_flag('blink_on_time',0.4)
machine.add_flag('blink_off_time',0.1)
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 5.0)
```

### handlers.py

```python
# firmware/fake/handlers.py
# Device-specific commands

def handle_blink(machine, payload):
    """
    Handles the device-specific 'blink' command.
    DOC: Blinks the onboard LED a specified number of times.
    ARGS:
      - count (integer, default: 1)
    """
    try:
        count = int(payload.get("args", [1])[0])
    except (ValueError, IndexError):
        count = 1
    
    machine.flags['blink_count'] = count
    machine.log.info(f"Blink request received for {count} times.")
    machine.go_to_state('Blinking')
```

### states.py

```python
# firmware/fake/states.py
# type: ignore
import time
import board
import digitalio
import analogio
from shared_lib.statemachine import State
from shared_lib.messages import Message

class Initialize(State):
    """
    Initializes the hardware (LED, ADC) required for the fake device.
    """
    @property
    def name(self):
        return 'Initialize'

    def enter(self, machine):
        super().enter(machine)
        # Setup hardware
        try:
            machine.led = digitalio.DigitalInOut(board.LED)
            machine.led.direction = digitalio.Direction.OUTPUT
            machine.led.value = False
            machine.analog_in = analogio.AnalogIn(board.A0)
            
            machine.log.info("Fake device initialized successfully.")
            machine.go_to_state('Idle')
        except Exception as e:
            # If any hardware is missing, go to a permanent error state
            machine.flags['error_message'] = str(e)
            machine.log.critical(f"Initialization failed: {e}")
            machine.go_to_state('Error')

class Blinking(State):
    """
    Handles the non-blocking logic for blinking the LED a set number of times.
    """
    @property
    def name(self):
        return 'Blinking'

    def enter(self, machine):
        """
        Called once when entering the Blinking state. Sets up the blink count
        and initializes the timer for the first toggle.
        """
        super().enter(machine)
        self.blinks_remaining = machine.flags.get('blink_count', 0)
        machine.log.info(f"Starting to blink {self.blinks_remaining} times.")
        
        # Handle the case where we are asked to blink 0 or fewer times.
        if self.blinks_remaining <= 0:
            machine.led.value = False # Ensure LED is off
            machine.go_to_state('Idle')
            return

        # --- THE FIX IS HERE ---
        # Start the first blink immediately and set the timer for the next toggle.
        machine.led.value = True
        # Initialize the 'next_toggle_time' attribute on self.
        self.next_toggle_time = time.monotonic() + machine.flags['blink_on_time'] # BLINK_ON_TIME

    def update(self, machine):
        """
        Called repeatedly. Checks the timer and toggles the LED or returns
        to Idle when complete.
        """
        # This check will now work correctly.
        if time.monotonic() >= self.next_toggle_time:
            # Toggle the LED
            machine.led.value = not machine.led.value
            
            if machine.led.value: # Just turned ON (start of a new cycle)
                self.next_toggle_time = time.monotonic() + machine.flags['blink_on_time'] # BLINK_ON_TIME
            else: # Just turned OFF (end of a cycle)
                self.blinks_remaining -= 1
                self.next_toggle_time = time.monotonic() + machine.flags['blink_off_time'] # BLINK_OFF_TIME

            # Check if all blink cycles are complete
            if self.blinks_remaining <= 0:
                machine.log.info("Blinking complete.")
                # Send a SUCCESS response back to the host
                response = Message.create_message(
                    subsystem_name=machine.name,
                    status="SUCCESS",
                    payload={"detail": f"Completed {machine.flags.get('blink_count', 0)} blinks."}
                )
                machine.postman.send(response.serialize())
                
                # Clean up and transition back to Idle
                machine.flags['blink_count'] = 0
                machine.led.value = False
                machine.go_to_state('Idle')

class Error(State):
    """
    A terminal state entered on critical failure (e.g., hardware init failed).
    """
    @property
    def name(self):
        return 'Error'
    
    def enter(self, machine):
        super().enter(machine)
        error_msg = machine.flags.get('error_message', "Unknown error.")
        machine.log.critical(f"ENTERING ERROR STATE: {error_msg}")
        # Turn LED on solid to indicate a persistent error
        if hasattr(machine, 'led'):
            machine.led.value = True

    def update(self, machine):
        # Stay in this state until the device is reset
        time.sleep(10)
```

## firmware\sidekick

### __init__.py

```python
# firmware/sidekick/__init__.py
# type: ignore
import board
from shared_lib.statemachine import StateMachine
from shared_lib.messages import Message
from communicate.circuitpython_postman import CircuitPythonPostman

# Import resources from our common firmware library
from firmware.common.common_states import GenericError
from firmware.common.command_library import register_common_commands

# Import the device-specific parts we will write
from . import states
from . import handlers
# In a real implementation, you would have a kinematics library. We'll stub this for now.
# import kinematicsfunctions as kf

# ============================================================================
# SIDEKICK INSTRUMENT CONFIGURATION
# ============================================================================
SIDEKICK_CONFIG = {
    "pins": {
        "motor1_step": board.GP1, "motor1_dir": board.GP0, "motor1_enable": board.GP7,
        "motor2_step": board.GP10, "motor2_dir": board.GP9, "motor2_enable": board.GP16,
        "motor1_m0": board.GP6, "motor1_m1": board.GP5,
        "motor2_m0": board.GP15, "motor2_m1": board.GP14,
        "endstop_m1": board.GP18, "endstop_m2": board.GP19,
        "user_button": board.GP20,
        "pump1": board.GP27, "pump2": board.GP26, "pump3": board.GP22, "pump4": board.GP21,
    },
    "motor_settings": {
        "step_angle_degrees": 0.9, "microsteps": 8, "max_speed_sps": 500,
    },
    "pump_timings": {
        "aspirate_time": 0.1, "dispense_time": 0.1, "increment_ul": 10.0,
    },
    "kinematics": {
        "L1": 7.0, "L2": 3.0, "L3": 10.0, "Ln": 0.5,
    },
    "safe_limits": {
        # These are now determined during the Homing state, but placeholders are good.
        "m1_max_steps": 16000, "m2_max_steps": 16000,
    },
    "home_position": {
        "x": 10.0, "y": 5.0
    },
    "pump_offsets": {
        "p1": {"dx": 0.5, "dy": 0.0}, "p2": {"dx": 0.0, "dy": 0.5},
        "p3": {"dx": -0.5, "dy": 0.0}, "p4": {"dx": 0.0, "dy": -0.5},
    }
}

# This callback defines the device's specific telemetry data.
def send_sidekick_telemetry(machine):
    # This assumes a function exists to convert motor steps to Cartesian coords.
    # For now, we'll send the raw steps.
    # pos_xy = kf.forward_kinematics(machine.flags['current_m1_steps'], ...)
    telemetry_message = Message.create_message(
        subsystem_name=machine.name,
        status="TELEMETRY",
        payload={
            "m1_steps": machine.flags.get('current_m1_steps'),
            "m2_steps": machine.flags.get('current_m2_steps')
            # "x": pos_xy['x'], "y": pos_xy['y'] # This would be the ideal implementation
        }
    )
    machine.postman.send(telemetry_message.serialize())

# 1. Create the state machine instance
machine = StateMachine(init_state='Initialize', name='SIDEKICK')

# 2. Attach the configuration and Postman
machine.config = SIDEKICK_CONFIG
postman = CircuitPythonPostman(params={"protocol": "serial_cp"})
postman.open_channel()
machine.postman = postman

# 3. Add all the states the machine can be in
machine.add_state(states.Initialize())
# AI Generated a custom Idle state, so we'll use that
#machine.add_state(states.Idle(telemetry_callback=send_sidekick_telemetry))
machine.add_state(states.Idle())
machine.add_state(states.Homing())
machine.add_state(states.Moving())
machine.add_state(states.Dispensing())
machine.add_state(GenericError())

# 4. Define the machine's command interface
register_common_commands(machine) # Adds 'ping' and 'help'
machine.add_command("home", handlers.handle_home, {
    "description": "Finds motor zero via endstops, then moves to a safe parking spot.",
    "args": []
})
machine.add_command("move_to", handlers.handle_move_to, {
    "description": "Moves the arm's center point to an absolute (x, y) coordinate.",
    "args": ["x: float", "y: float"]
})
machine.add_command("move_rel", handlers.handle_move_rel, {
    "description": "Moves the arm relative to its current position by (dx, dy).",
    "args": ["dx: float", "dy: float"]
})
machine.add_command("dispense", handlers.handle_dispense, {
    "description": "Dispenses from a pump at the current location (includes offset move).",
    "args": ["pump: str (e.g., 'p1')", "vol: float"]
})
machine.add_command("dispense_at", handlers.handle_dispense_at, {
    "description": "Moves a pump to an absolute (x, y) coordinate and then dispenses.",
    "args": ["pump: str", "vol: float", "x: float", "y: float"]
})
machine.add_command("steps", handlers.handle_steps, {
    "description": "Moves motors by a relative number of steps. FOR TESTING ONLY.",
    "args": ["m1: int", "m2: int"]
})

# 5. Add dynamic flags (values that will change during operation)
machine.add_flag('is_homed', False)
machine.add_flag('error_message', '')
machine.add_flag('telemetry_interval', 2.0)
machine.add_flag('current_m1_steps', 0)
machine.add_flag('current_m2_steps', 0)
machine.add_flag('target_m1_steps', 0)
machine.add_flag('target_m2_steps', 0)
machine.add_flag('dispense_pump', None)
machine.add_flag('dispense_cycles', 0)
machine.add_flag('on_move_complete', None) # For the state sequencer
```

### handlers.py

```python
# firmware/sidekick/handlers.py
# type: ignore
from shared_lib.messages import Message
# In a real implementation, a kinematics library would live in shared_lib or firmware/common
# import kinematicsfunctions as kf

# --- Utility Functions for Handlers ---
def send_problem(machine, error_msg):
    """Helper to send a standardized PROBLEM message."""
    machine.log.error(error_msg)
    response = Message.create_message(
        subsystem_name=machine.name,
        status="PROBLEM",
        payload={"error": error_msg}
    )
    machine.postman.send(response.serialize())

def check_homed(machine):
    """Guard condition to ensure the device is homed."""
    if not machine.flags.get('is_homed', False):
        send_problem(machine, "Device must be homed before this operation.")
        return False
    return True

# --- Command Handlers ---

def handle_home(machine, payload):
    machine.log.info("Home command received.")
    machine.go_to_state('Homing')

def handle_move_to(machine, payload):
    if not check_homed(machine): return
    
    # Placeholder for coordinate validation and conversion
    # target_steps = kf.inverse_kinematics(payload['x'], payload['y'])
    # if not kf.is_within_limits(target_steps):
    #     send_problem(machine, "Target coordinates are out of safe travel limits.")
    #     return
    
    # For now, we will assume target steps are provided directly for testing
    target_m1 = payload.get('m1_steps', 0)
    target_m2 = payload.get('m2_steps', 0)

    machine.log.info(f"Move_to command accepted. Target: ({target_m1}, {target_m2}) steps.")
    machine.flags['target_m1_steps'] = target_m1
    machine.flags['target_m2_steps'] = target_m2
    machine.flags['on_move_complete'] = 'Idle' # Default exit for a simple move
    machine.go_to_state('Moving')

def handle_move_rel(machine, payload):
    if not check_homed(machine): return
    # Placeholder for relative move calculation
    # target_x = machine.flags['current_x'] + payload['dx']
    # Perform validation on target_x, then convert to steps
    send_problem(machine, "move_rel not yet implemented.")

def handle_dispense(machine, payload):
    if not check_homed(machine): return
    
    pump = payload.get('pump')
    vol = payload.get('vol')
    
    if pump not in machine.config['pump_offsets']:
        send_problem(machine, f"Invalid pump specified: {pump}")
        return

    # Round volume down to the nearest increment
    increment = machine.config['pump_timings']['increment_ul']
    cycles = int(vol // increment)
    if cycles * increment != vol:
        machine.log.warning(f"Volume {vol}uL not a multiple of {increment}uL. Dispensing {cycles * increment}uL.")

    if cycles <= 0:
        send_problem(machine, "Volume is too low to dispense.")
        return
        
    # This command uses the state sequencer.
    # For now, we'll just set the flags and transition directly.
    # A real implementation would calculate an offset move first.
    machine.log.info(f"Dispense command accepted for pump {pump}, {cycles} cycles.")
    machine.flags['dispense_pump'] = pump
    machine.flags['dispense_cycles'] = cycles
    machine.go_to_state('Dispensing')

def handle_dispense_at(machine, payload):
    if not check_homed(machine): return
    
    # This is the most complex handler. It sets up a multi-state sequence.
    # 1. Validate all parameters
    # 2. Calculate target motor steps from x, y
    # 3. Set machine.flags['target..._steps']
    # 4. Set machine.flags['dispense_pump'] and ['dispense_cycles']
    # 5. Set the sequencer flag: machine.flags['on_move_complete'] = 'Dispensing'
    # 6. Go to the first state in the sequence: machine.go_to_state('Moving')
    
    send_problem(machine, "dispense_at not yet implemented.")

def handle_steps(machine, payload):
    """
    Handles the low-level 'steps' command for relative motor movement.
    This command bypasses the standard homing and safety checks.
    """
    m1_rel_steps = payload.get('m1', 0)
    m2_rel_steps = payload.get('m2', 0)

    # Calculate the absolute target position from the current position
    # AI may be thinking absolute positions, so this is modified
    target_m1 = machine.flags['current_m1_steps'] + m1_rel_steps
    target_m2 = machine.flags['current_m2_steps'] + m2_rel_steps
    # target_m1 = m1_rel_steps
    # target_m2 = m2_rel_steps

    machine.log.info(f"Steps command accepted. Moving to ({target_m1}, {target_m2}).")
    
    # Set the flags that the 'Moving' state will use
    machine.flags['target_m1_steps'] = target_m1
    machine.flags['target_m2_steps'] = target_m2
    machine.flags['on_move_complete'] = 'Idle' # Tell the sequencer to return to Idle when done

    machine.go_to_state('Moving')
```

### states.py

```python
# firmware/sidekick/states.py
# type: ignore
import time
import digitalio
from shared_lib.statemachine import State
from shared_lib.messages import Message
from firmware.common.common_states import listen_for_instructions

class Initialize(State):
    @property
    def name(self): return 'Initialize'
    def enter(self, machine):
        super().enter(machine)
        try:
            # Create a dictionary of all hardware objects for easy access
            machine.hardware = {}
            pin_config = machine.config['pins']
            
            # Setup Motors and Endstops
            for i in [1, 2]:
                machine.hardware[f'motor{i}_step'] = digitalio.DigitalInOut(pin_config[f'motor{i}_step'])
                machine.hardware[f'motor{i}_step'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_dir'] = digitalio.DigitalInOut(pin_config[f'motor{i}_dir'])
                machine.hardware[f'motor{i}_dir'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_enable'] = digitalio.DigitalInOut(pin_config[f'motor{i}_enable'])
                machine.hardware[f'motor{i}_enable'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_enable'].value = True # Start with motors disabled (HIGH = off for some drivers)

                machine.hardware[f'endstop_m{i}'] = digitalio.DigitalInOut(pin_config[f'endstop_m{i}'])
                machine.hardware[f'endstop_m{i}'].direction = digitalio.Direction.INPUT
                machine.hardware[f'endstop_m{i}'].pull = digitalio.Pull.UP
            
            # Setup Pumps
            machine.hardware['pumps'] = {}
            for i in [1, 2, 3, 4]:
                machine.hardware['pumps'][f'p{i}'] = digitalio.DigitalInOut(pin_config[f'pump{i}'])
                machine.hardware['pumps'][f'p{i}'].direction = digitalio.Direction.OUTPUT

            machine.log.info("Sidekick hardware initialized successfully.")
            machine.go_to_state('Homing') # The first action after init must be to home.
        except Exception as e:
            machine.flags['error_message'] = f"Hardware Initialization failed: {e}"
            machine.go_to_state('Error')

class Idle(State):
    @property
    def name(self): return 'Idle'
    def __init__(self, telemetry_callback=None):
        super().__init__()
        self._telemetry_callback = telemetry_callback
    def enter(self, machine):
        super().enter(machine)
        self._telemetry_interval = machine.flags.get('telemetry_interval', 5.0)
        self._next_telemetry_time = time.monotonic() + self._telemetry_interval
        machine.hardware['motor1_enable'].value = True # Disable motors to save power
        machine.hardware['motor2_enable'].value = True
    def update(self, machine):
        super().update(machine)
        listen_for_instructions(machine)
        if time.monotonic() >= self._next_telemetry_time:
            if self._telemetry_callback:
                self._telemetry_callback(machine)
            self._next_telemetry_time = time.monotonic() + self._telemetry_interval

class Homing(State):
    @property
    def name(self): return 'Homing'
    # This is a placeholder. A real implementation would be more complex,
    # moving one motor at a time and handling timeouts.
    def enter(self, machine):
        super().enter(machine)
        machine.log.info("Homing sequence started...")
        # For now, we will simulate a successful home.
        machine.flags['is_homed'] = True
        machine.flags['current_m1_steps'] = 0
        machine.flags['current_m2_steps'] = 0
        machine.log.info("Homing complete (simulated).")
        # In a real implementation, you would then move to the parking spot.
        machine.go_to_state('Idle')
    def update(self, machine):
        pass # The enter method does everything for this simple simulation

class Moving(State):
    """
    The 'Motion Engine' state. It executes a planned move from a start point
    to a target point in a non-blocking way.
    """
    @property
    def name(self): return 'Moving'

    def enter(self, machine):
        """
        Called once on entry. This is where we plan the entire move.
        """
        super().enter(machine)
        
        # 1. Read start and target positions from the machine's flags
        start_m1 = machine.flags['current_m1_steps']
        start_m2 = machine.flags['current_m2_steps']
        self.target_m1 = machine.flags['target_m1_steps']
        self.target_m2 = machine.flags['target_m2_steps']
        
        machine.log.info(f"Moving from ({start_m1}, {start_m2}) to ({self.target_m1}, {self.target_m2}).")

        # 2. Calculate the plan: steps and direction for each motor
        delta_m1 = self.target_m1 - start_m1
        delta_m2 = self.target_m2 - start_m2
        
        self.steps_left_m1 = abs(delta_m1)
        self.steps_left_m2 = abs(delta_m2)
        
        # Set motor direction pins (True/False may need to be adjusted for your wiring)
        machine.hardware['motor1_dir'].value = True if delta_m1 > 0 else False
        machine.hardware['motor2_dir'].value = True if delta_m2 > 0 else False

        # 3. Enable the motors
        machine.hardware['motor1_enable'].value = False
        machine.hardware['motor2_enable'].value = False
        time.sleep(0.01) # Short delay to ensure drivers are fully enabled

    def update(self, machine):
        """
        Called on every loop. This is the core stepper pulse generator.
        This is a simple implementation that steps both motors on each loop.
        A more advanced version would use Bresenham's algorithm for smoother lines.
        """
        super().update(machine)
        
        # Check for unexpected endstops (Safety First!)
        # Note: Endstop value is False when pressed due to Pull.UP
        if not machine.hardware['endstop_m1'].value or not machine.hardware['endstop_m2'].value:
            machine.hardware['motor1_enable'].value = True # Immediately disable motors
            machine.hardware['motor2_enable'].value = True
            machine.flags['is_homed'] = False # We no longer know our position
            machine.flags['error_message'] = "FAULT: Endstop triggered during move!"
            machine.go_to_state('Error')
            return # Stop processing immediately

        move_is_done = True
        
        # Pulse Motor 1 if it still has steps to go
        if self.steps_left_m1 > 0:
            step_pin = machine.hardware['motor1_step']
            step_pin.value = True
            step_pin.value = False # This pulse is very short
            self.steps_left_m1 -= 1
            move_is_done = False
        
        # Pulse Motor 2 if it still has steps to go
        if self.steps_left_m2 > 0:
            step_pin = machine.hardware['motor2_step']
            step_pin.value = True
            step_pin.value = False
            self.steps_left_m2 -= 1
            move_is_done = False
            
        # If both motors have completed their moves
        if move_is_done:
            # Update the final position in the machine's flags
            machine.flags['current_m1_steps'] = self.target_m1
            machine.flags['current_m2_steps'] = self.target_m2

            # Use the State Sequencer to decide where to go next
            next_state = machine.flags.get('on_move_complete', 'Idle')
            machine.flags['on_move_complete'] = None # Clear the flag for the next command
            
            machine.log.info(f"Move complete. Transitioning to '{next_state}'.")
            machine.go_to_state(next_state)

    def exit(self, machine):
        """
        Called once on exit. Ensures motors are disabled to save power.
        """
        super().exit(machine)
        machine.hardware['motor1_enable'].value = True
        machine.hardware['motor2_enable'].value = True

class Dispensing(State):
    @property
    def name(self): return 'Dispensing'
    def enter(self, machine):
        super().enter(machine)
        self.pump_key = machine.flags.get('dispense_pump')
        self.cycles_left = machine.flags.get('dispense_cycles')
        self.pump_pin = machine.hardware['pumps'][self.pump_key]
        self.pump_state = 'aspirating'
        self.timings = machine.config['pump_timings']
        
        machine.log.info(f"Dispensing {self.cycles_left} cycles from {self.pump_key}.")
        # Start the first aspirate cycle
        self.pump_pin.value = True
        self._next_toggle_time = time.monotonic() + self.timings['aspirate_time']

    def update(self, machine):
        if time.monotonic() >= self._next_toggle_time:
            if self.pump_state == 'aspirating':
                self.pump_pin.value = False
                self.pump_state = 'dispensing'
                self._next_toggle_time = time.monotonic() + self.timings['dispense_time']
                self.cycles_left -= 1
            elif self.pump_state == 'dispensing':
                if self.cycles_left > 0:
                    self.pump_pin.value = True
                    self.pump_state = 'aspirating'
                    self._next_toggle_time = time.monotonic() + self.timings['aspirate_time']
                else:
                    # We are finished
                    machine.log.info("Dispense complete.")
                    response = Message.create_message(
                        subsystem_name=machine.name,
                        status="SUCCESS",
                        payload={"pump": self.pump_key, "cycles": machine.flags.get('dispense_cycles')}
                    )
                    machine.postman.send(response.serialize())
                    machine.go_to_state('Idle')
```

## host_app

### __init__.py

```python

```

### config.py

```python

```

### firmware_db.py

```python
# host_app/firmware_db.py

FIRMWARE_DATABASE = {
    808: {
        'manufacturer': 'Brockport Original Builds',
        'products': {
            810: 'Fake Device',
            811: 'DIY Stirplate', 
            812: 'Sidekick dispenser',
            813: 'Colorimeter'
        }
    },
    # 909: {
    #     'manufacturer': 'My Lab',
    #     'products': {
    #         909: 'Heater Control Unit',
    #     }
    # }
}

def get_device_name(vid: int, pid: int) -> str:
    """
    Looks up a human-readable name for a device based on its VID and PID.
    
    Returns a descriptive string or a default if not found.
    """
    manufacturer_info = FIRMWARE_DATABASE.get(vid)
    
    if not manufacturer_info:
        return "Unknown Manufacturer"
        
    product_name = manufacturer_info['products'].get(pid, "Unknown Product")
    manufacturer_name = manufacturer_info.get('manufacturer', "Unknown")
    
    return f"{product_name} ({manufacturer_name})"
```

### main.py

```python

```

## host_app\devices

### __init__.py

```python

```

### fake_device.py

```python
# host_app/devices/fake_device.py
import logging
from shared_lib.message_buffer import LinearMessageBuffer
from communicate.postman import DummyPostman
from communicate.secretary import SecretaryStateMachine, Router, CircularFiler
from shared_lib.statemachine import State, StateMachine
from shared_lib.messages import Message
import json

# Set up logging for the fake device
# NOTE: Using a basicConfig here can sometimes interfere with other logging configurations.
# For a larger application, it's often better to configure logging at the entry point (main.py).
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger("FakeDevice")

class FakeInstrumentSubsystemRouter(Router):
    """
    A simple router for the FakeDevice. In a real device, this would
    direct messages to specific hardware control state machines.
    For the fake device, we'll just log and maybe simulate a response.
    """
    def __init__(self, device_name: str, outbox: LinearMessageBuffer):
        self.device_name = device_name
        self.outbox = outbox
        log.info(f"Router for {device_name} initialized.")

    def route(self, message: Message):
        log.info(f"FakeInstrumentRouter received message for '{self.device_name}': {message.to_dict()}")
        # Simulate a response to an "INSTRUCTION"
        if message.status == "INSTRUCTION":
            payload_data = message.payload # Assuming payload is already a dict
            log.info(f"FakeInstrumentRouter: Processing instruction payload: {payload_data}")

            # Example: Simulate turning on/off an LED
            if isinstance(payload_data, dict) and payload_data.get("func") == "set_led":
                led_state = payload_data.get("args", ["off"])[0] # Get first arg, default 'off'
                response_payload = {"status": "LED set to " + str(led_state)}
                response_status = "SUCCESS"
                log.info(f"FakeInstrument: LED is now {led_state}")
            else:
                response_payload = {"error": "Unknown instruction or malformed payload."}
                response_status = "PROBLEM"

            # Create a response message
            response_message = Message.create_message(
                subsystem_name=self.device_name,
                status=response_status,
                payload=response_payload
            )
            self.outbox.store(response_message)
            log.info(f"FakeInstrumentRouter: Stored response in outbox: {response_message.to_dict()}")
        # else: Just acknowledge other messages (HEARTBEAT, INFO) without response

class FakeDevice:
    """
    A software-only representation of a scientific instrument.
    It uses a DummyPostman to simulate serial communication.
    """
    def __init__(self, name="FakeInstrument"):
        self.name = name
        self.postman = DummyPostman(params={"protocol": "dummy"})
        self.postman.open_channel()
        self.inbox = LinearMessageBuffer()
        self.outbox = LinearMessageBuffer()
        self.subsystem_router = FakeInstrumentSubsystemRouter(name, self.outbox)
        # Using a base Filer that does nothing, as CircularFiler prints. For tests, silence is better.
        self.filer = CircularFiler({'print': False})
        self.secretary = SecretaryStateMachine(
            inbox=self.inbox,
            outbox=self.outbox,
            subsystem_router=self.subsystem_router,
            filer=self.filer,
            postman=self.postman,
            name=f"{self.name}_Secretary"
        )
        self.secretary.run() # Start the secretary's state machine

        log.info(f"FakeDevice '{self.name}' initialized with DummyPostman.")

    def send_command(self, payload_dict: dict):
        """
        Simulates sending a command *to* the fake device.
        This will be received by its internal DummyPostman.
        """
        cmd_message = Message.create_message(
            subsystem_name="HOST", # Message is from the host
            status="INSTRUCTION",
            payload=payload_dict
        )
        # Store message in the DummyPostman's canned_responses buffer
        # This simulates the host sending a message that the device's Postman will receive
        self.postman.canned_responses.append(cmd_message.serialize())
        log.info(f"Host: Sent command to FakeDevice: {cmd_message.to_dict()}")


    def read_responses(self):
        """
        Reads any messages the fake device has sent back via its DummyPostman.
        DEPRECATED in favor of get_sent_by_fake_device which is more explicit.
        """
        return self.get_sent_by_fake_device()

    def update(self):
        """
        Simulates the device's main loop.
        1. Check for incoming data from the postman (as a raw string).
        2. If data exists, parse it into a Message object.
        3. Place the Message object in the secretary's inbox.
        4. Update the secretary state machine, which will now process it.
        """
        # Step 1: Check for incoming messages from the "outside world"
        raw_incoming_message = self.postman.receive() # Pulls from canned_responses
        if raw_incoming_message:
            log.info(f"FakeDevice: Received raw message from Postman: {raw_incoming_message}")
            try:
                # Step 2 & 3: Parse the message and store it in the secretary's inbox
                message = Message.from_json(raw_incoming_message)
                self.secretary.inbox.store(message) # Store the PARSED message object
            except (ValueError, json.JSONDecodeError) as e:
                log.error(f"Failed to parse incoming message: {raw_incoming_message}. Error: {e}")

        # Step 4: Now, update the secretary. If a message was stored, it will process it.
        self.secretary.update()

    def get_sent_by_fake_device(self):
        """
        Retrieve messages the fake device has "sent" out (which means they are
        in the DummyPostman's sent_values list).
        """
        sent_messages = []
        # get_sent_values() returns a list of raw JSON strings
        for raw_msg_str in self.postman.get_sent_values():
            try:
                # We need to parse the JSON string back into a Message object
                msg = Message.from_json(raw_msg_str)
                sent_messages.append(msg)
            except (ValueError, json.JSONDecodeError) as e:
                log.error(f"Failed to parse sent message: {raw_msg_str}. Error: {e}")
        self.postman.clear_sent_values() # Clear after reading
        return sent_messages

    def stop(self):
        self.secretary.stop()
        log.info(f"FakeDevice '{self.name}' stopped.")
```

## host_app\gui

### __init__.py

```python

```

### host_interface.py

```python
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import threading
import time
from datetime import datetime
from ..firmware_db import get_device_name
from communicate.host_utilities import find_data_comports
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message

class SimpleHostGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Self-Driving Lab: Host Interface")
        self.root.geometry("800x600")

        # --- State Variables ---
        self.postman = None
        self.is_connected = False
        self.worker_thread = None
        self.stop_thread = threading.Event()
        self.available_devices = []  # --- MODIFIED ---: Will store the list of full device dicts

        # --- UI Setup ---
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        # --- Connection Frame ---
        conn_frame = ttk.LabelFrame(self.root, text="Connection", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(conn_frame, text="Available Devices:").pack(side=tk.LEFT, padx=5)
        self.device_combo = ttk.Combobox(conn_frame, state="readonly")
        self.device_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.scan_btn = ttk.Button(conn_frame, text="Scan for Devices", command=self.scan_ports)
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_device)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_device, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        # ... (rest of the widget creation is the same) ...
        # --- Log Frame ---
        log_frame = ttk.LabelFrame(self.root, text="Incoming Messages", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- Command Frame ---
        cmd_frame = ttk.LabelFrame(self.root, text="Send Command", padding=10)
        cmd_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(cmd_frame, text="Payload (JSON):").pack(side=tk.LEFT, padx=5)
        self.payload_entry = ttk.Entry(cmd_frame)
        self.payload_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.payload_entry.insert(0, '{"func": "blink", "args": [3]}')
        
        self.send_btn = ttk.Button(cmd_frame, text="Send Instruction", command=self.send_command, state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self.root, text="Status: Disconnected", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def log_message(self, text, prefix=""):
        # ... (this method is unchanged) ...
        def _do_log():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            full_message = f"[{timestamp}] {prefix}{text}\n"
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, full_message)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(0, _do_log)

    def scan_ports(self):
        # --- MODIFIED ---: This whole method is updated to use the database.
        self.log_message("Scanning for CircuitPython devices...")
        try:
            self.available_devices = find_data_comports()
            
            # Use get_device_name to create rich, descriptive names for the UI
            display_strings = []
            for p in self.available_devices:
                friendly_name = get_device_name(p['VID'], p['PID'])
                display_str = f"{friendly_name} - {p['port']} (VID:{p['VID']}, PID:{p['PID']})"
                display_strings.append(display_str)

            self.device_combo['values'] = display_strings
            if display_strings:
                self.device_combo.current(0)
                self.log_message(f"Found {len(display_strings)} device(s).")
            else:
                self.log_message("No devices found.")
                self.available_devices = []
        except Exception as e:
            self.log_message(f"Error scanning for ports: {e}", prefix="ERROR: ")
            self.available_devices = []

    def connect_device(self):
        # --- MODIFIED ---: Logic to get the port name is updated.
        selected_index = self.device_combo.current()

        if selected_index == -1:  # -1 means no item is selected
            self.log_message("No device selected.", prefix="ERROR: ")
            return

        # Retrieve the full device info using the index
        device_info = self.available_devices[selected_index]
        port = device_info['port']  # Extract just the port name for the connection
        
        if self.is_connected:
            self.log_message("Already connected.", prefix="WARNING: ")
            return

        try:
            self.log_message(f"Attempting to connect to {port}...")
            params = {"protocol": "serial", "port": port, "baudrate": 115200, "timeout": 0.1}
            self.postman = SerialPostman(params)
            self.postman.open_channel()
            
            time.sleep(1)
            self.postman.channel.reset_input_buffer()
            
            self.is_connected = True
            self.stop_thread.clear()
            
            self.worker_thread = threading.Thread(target=self._message_receiver_loop, daemon=True)
            self.worker_thread.start()
            
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.send_btn.config(state=tk.NORMAL)
            self.device_combo.config(state=tk.DISABLED)
            self.scan_btn.config(state=tk.DISABLED)
            # Use the friendly name from the combobox for the status bar
            self.status_bar.config(text=f"Status: Connected to {self.device_combo.get()}")
            self.log_message(f"Successfully connected to {port}.")
        except Exception as e:
            self.log_message(f"Failed to connect: {e}", prefix="ERROR: ")
            if self.postman:
                self.postman.close_channel()
            self.postman = None
    
    # --- NO OTHER CHANGES ARE NEEDED BELOW THIS LINE ---
    
    def _message_receiver_loop(self):
        while not self.stop_thread.is_set():
            if self.postman and self.postman.is_open:
                try:
                    raw_data = self.postman.receive()
                    if raw_data:
                        try:
                            msg = Message.from_json(raw_data)
                            self.log_message(f"Received: {msg.to_dict()}", prefix="RECV: ")
                        except (json.JSONDecodeError, ValueError):
                            self.log_message(f"Received raw data: {raw_data}", prefix="RECV: ")
                except Exception as e:
                    self.log_message(f"Error in receive loop: {e}", prefix="ERROR: ")
                    self.stop_thread.set()
            
            time.sleep(0.05)
        
        self.log_message("Message receiver thread stopped.")

    def disconnect_device(self):
        if not self.is_connected:
            return

        self.log_message("Disconnecting...")
        self.stop_thread.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        
        if self.postman:
            self.postman.close_channel()

        self.is_connected = False
        self.postman = None
        
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.device_combo.config(state="readonly")
        self.scan_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="Status: Disconnected")
        self.log_message("Disconnected successfully.")

    def send_command(self):
        if not self.is_connected:
            self.log_message("Not connected. Cannot send command.", prefix="ERROR: ")
            return

        payload_str = self.payload_entry.get()
        try:
            payload_dict = json.loads(payload_str)
            message = Message.create_message(
                subsystem_name="HOST",
                status="INSTRUCTION",
                payload=payload_dict
            )
            serialized_msg = message.serialize()
            self.postman.send(serialized_msg)
            self.log_message(f"Sent: {message.to_dict()}", prefix="SENT: ")
        except json.JSONDecodeError:
            self.log_message(f"Invalid JSON in payload: {payload_str}", prefix="ERROR: ")
        except Exception as e:
            self.log_message(f"Failed to send command: {e}", prefix="ERROR: ")

    def on_closing(self):
        if self.is_connected:
            self.disconnect_device()
        self.root.destroy()

if __name__ == "__main__":
    app_root = tk.Tk()
    gui = SimpleHostGUI(app_root)
    app_root.mainloop()
```

## host_app\processors

### __init__.py

```python

```

## host_app\services

### __init__.py

```python

```

## shared_lib

### __init__.py

```python

```

### message_buffer.py

```python
#type: ignore

# Base (abstract-ish) class for a buffer that will handle messages.
class MessageBuffer():
    """
    Base class for message buffer implementations.
    """

    def __init__(self, max_size: int = 100):
        """
        Initializes the message buffer.
        """
        self.messages = self._create_storage()  # Abstract method to create storage
        self.max_size = max_size  # Maximum capacity of the buffer (fixed)
        self.current_size = 0  # Track how many messages are in the buffer.  Important for Circular Buffer
        #This is for the circular buffer, but it won't hurt the others.
        self.head = 0
        self.tail = 0

    def is_empty(self) -> bool:
        """
        Returns True if the buffer is empty, False otherwise.
        """
        return self.current_size == 0

    def is_full(self) -> bool:
        """
        Returns True if the buffer is full, False otherwise.
        """
        return self.current_size >= self.max_size

    def store(self, value):
        """
        Stores a value in the message buffer.
        """
        if self.is_full():
            self._handle_full_buffer(value) # handle the exception if the buffer is full
            return
        self._store(value) #Implementation specific storing
        self.current_size += 1

    def get(self):
        """
        Retrieves the next message from the buffer (implementation-specific).
        """
        if self.is_empty():
            return None  # Or raise an exception if appropriate

        value = self._get() #Implementation specific retreival
        self.current_size -= 1
        return value

    def flush(self):
        """
        Empties the buffer.
        """
        self._flush() #Implementation specific flushing
        self.current_size = 0
        self.head = 0
        self.tail = 0

    def _create_storage(self):
      """Creates a new storage object"""
      return [] # implementation specific

    def _handle_full_buffer(self, value):
        """handles when the message buffer is full"""
        raise OverflowError("Buffer is full")

    def _store(self, value):
        """Stores a value in the buffer, Implementation Specific"""
        raise NotImplementedError("Implementation specific storing not implemented")

    def _get(self):
        """Retrieves a value from the buffer, Implementation Specific"""
        raise NotImplementedError("Implementation specific retrieval not implemented")

    def _flush(self):
        """flushes, implementation specific"""
        raise NotImplementedError("Implementation specific flush not implemented")

class LinearMessageBuffer(MessageBuffer):
    """
    A simple linear FIFO message buffer implemented using a list.
    """

    def __init__(self, max_size: int = 100):
        super().__init__(max_size)
    
    def _create_storage(self):
        return []

    def _store(self, value):
        self.messages.append(value)

    def _get(self):
        return self.messages.pop(0)

    def _flush(self):
        self.messages = []


class CircularMessageBuffer(MessageBuffer):
    """
    A circular FIFO message buffer implemented using a list.
    """

    def __init__(self, max_size: int = 100):
        super().__init__(max_size)
        
    def _create_storage(self):
        return [None] * self.max_size #initialize with None

    def _handle_full_buffer(self, value):
        self._get() #this handles the exception that happens on this circular buffer

    def _store(self, value):
        self.messages[self.tail] = value
        self.tail = (self.tail + 1) % self.max_size

        if self.is_full():
            self.head = (self.head + 1) % self.max_size # If full, also advance the head

    def _get(self):
        if self.is_empty():
            return None  # Or raise an exception if appropriate

        value = self.messages[self.head]
        self.messages[self.head] = None # clean the previous data
        self.head = (self.head + 1) % self.max_size
        return value

    def _flush(self):
        self.messages = [None] * self.max_size
        self.head = 0
        self.tail = 0
```

### messages.py

```python
#type: ignore
import json


class Message():
    """
    Represents a message with subsystem name, status, metadata, and payload.
    """

    VALID_STATUS = {"DEBUG", "TELEMETRY", "INFO", "INSTRUCTION", "SUCCESS", "PROBLEM", "WARNING"}

    def __init__(self, subsystem_name=None, status=None, meta=None, payload=None):
        """Initializes a Message object."""
        self._subsystem_name = subsystem_name
        # Validate that the status provided to the method is valid
        if status is not None and status not in Message.VALID_STATUS:
           raise ValueError("Invalid Status Level")
        self._status = status
        if meta is None:
            self._meta = {}
        elif not isinstance(meta, dict):
            raise TypeError("meta must be a dictionary")
        else:
            self._meta = meta
        self._payload = payload

    def to_dict(self):
        """Returns a dictionary representation of the message."""
        return {
            "subsystem_name": self.subsystem_name,
            "status": self.status,
            "meta": self.meta,
            "payload": self.payload
        }

    def serialize(self):
        """Serializes the message to JSON."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_string: str):
        """
        Creates a new Message instance from a JSON string.
        This is a class method.
        """
        try:
            data = json.loads(json_string)
            subsystem_name = data.get("subsystem_name")
            status = data.get("status")
            meta = data.get("meta", {})
            payload = data.get("payload")

            # The validation for status is handled by the __init__ method,
            # so we just pass the values along.
            return cls(
                subsystem_name=subsystem_name,
                status=status,
                meta=meta,
                payload=payload
            )
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")

    @property
    def subsystem_name(self):
        return self._subsystem_name

    @subsystem_name.setter
    def subsystem_name(self, value):
        self._subsystem_name = value

    @property
    def status(self):
        return self._status

    # Remove the setter
    # @status.setter
    # def status(self, value):
    #     #Validate that we can set it if its a valid status
    #     if value is not None and value not in Message.VALID_STATUS:
    #         raise ValueError("Invalid Status Level")
    #     self._status = value

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, value):
        if not isinstance(value, dict):
            raise TypeError("meta must be a dictionary")
        self._meta = value

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    @classmethod
    def create_message(cls, subsystem_name=None, status=None, meta=None, payload=None):
        """Creates a Message instance."""
        return cls(subsystem_name=subsystem_name, status=status, meta=meta, payload=payload)

    @classmethod
    def get_valid_status(cls):
        return cls.VALID_STATUS


```

### statemachine.py

```python
#type: ignore
"""
Classes to treat the software-driven laboratory subsystems as state machines

Author(s): BoB LeSuer
"""
from .utility import check_if_microcontroller
from .message_buffer import LinearMessageBuffer # Keep it simple, although at some point, SM should be able to choose
from time import monotonic

if check_if_microcontroller():
    import adafruit_logging as logging
else:
    import logging

class StateMachine:
    """
    A class to represent a state machine.

    Attributes:
    -----------
    state : State
        The current state of the state machine.
    states : dict
        A dictionary of all states in the state machine.
    flags : dict
        A dictionary of flags used in the state machine.
    running : bool
        Indicates whether the state machine is running.
    is_microcontroller : bool
        Indicates whether the system is a microcontroller.
    init_state : str
        The initial state of the state machine.

    Methods:
    --------
    add_state(state):
        Adds a state to the state machine.
    add_flag(flag, init_value):
        Adds a flag to the state machine.
    go_to_state(state_name):
        Transitions the state machine to the specified state.
    update():
        Updates the current state of the state machine.
    run(state_name=None):
        Starts the state machine.
    stop():
        Stops the state machine.
    """

    def __init__(self, init_state='Initialize', name=None):
        """
        Constructs all the necessary attributes for the state machine object.

        Parameters:
        -----------
        init_state : str, optional
            The initial state of the state machine (default is 'Initialize').
        """
        self.state = None
        self.states = {}
        self.flags = {} 
        self.command_handlers = {}
        self.supported_commands = {}
        self.running = False
        self.is_microcontroller = check_if_microcontroller()
        self.init_state = init_state
        self.name = name
        # Each state machine has an inbox
        self.inbox = LinearMessageBuffer()
        # TODO: Create a custom handler or other solution to address that adafruit_logging doesn't have basicConfig
        if not self.is_microcontroller:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)s] %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(self.name)

    def add_command(self, name: str, handler, doc: dict):
        """Adds a command handler and its documentation to the machine."""
        self.command_handlers[name] = handler
        self.supported_commands[name] = doc
        
    def handle_instruction(self, payload: dict):
        """Dispatches an instruction payload to the correct handler."""
        # Handler should set any flags and move to a different state
        
        func_name = payload.get("func") if isinstance(payload, dict) else None
        
        handler = self.command_handlers.get(func_name)
        
        if handler:
            # Call the handler, passing the machine instance and payload
            handler(self, payload)
        else:
            self._handle_unknown(payload)
            
    def _handle_unknown(self, payload):
        """Default handler for any command not found."""
        from .messages import Message # Local import for CircuitPython memory optimization
        func_name = payload.get("func") if payload else "N/A"
        self.log.error(f"Received an unknown instruction: {func_name}")
        response = Message.create_message(
            subsystem_name=self.name,
            status="PROBLEM",
            payload={"error": f"Unknown instruction: {func_name}"}
        )
        if hasattr(self, 'postman'):
            self.postman.send(response.serialize())


    def add_state(self, state):
        """
        Adds a state to the state machine.

        Parameters:
        -----------
        state : State
            The state to be added.
        """
        self.states[state.name] = state

    # Would eventually want the ability to add flags during state instantiation 
    def add_flag(self, flag, init_value):
        """
        Adds a flag to the state machine.

        Parameters:
        -----------
        flag : str
            The name of the flag.
        init_value : any
            The initial value of the flag.
        """
        self.flags[flag] = init_value

    def go_to_state(self, state_name):
        """
        Transitions the state machine to the specified state.

        Parameters:
        -----------
        state_name : str
            The name of the state to transition to.

        Raises:
        -------
        Exception:
            If the state machine is not running.
        """
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]
        self.state.enter(self)

    def update(self):
        """
        Updates the current state of the state machine.

        Raises:
        -------
        Exception:
            If the state machine is not running.
        """
        if not self.running:
            raise Exception('State machine must be running to do this.')
        if self.state:
            self.state.update(self)

    def run(self, state_name=None):
        """
        Starts the state machine.

        Parameters:
        -----------
        state_name : str, optional
            The name of the state to start with (default is None).
        """
        self.running = True
        if state_name is None:
            self.go_to_state(self.init_state)
        else:
            self.go_to_state(state_name)

    def stop(self):
        """
        Stops the state machine.
        """
        self.running = False


class State:
    """
    A class to represent a state in the state machine.

    Attributes:
    -----------
    entered_at : float
        The time when the state was entered.

    Methods:
    --------
    name():
        Returns the name of the state.
    enter(machine):
        Actions to perform when entering the state.
    exit(machine):
        Actions to perform when exiting the state.
    update(machine):
        Actions to perform when updating the state.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the state object.
        """
        self.entered_at = 0
 
    @property
    def name(self):
        """
        Returns the name of the state.

        Returns:
        --------
        str:
            The name of the state.
        """
        return ''

    def enter(self, machine):
        """
        Actions to perform when entering the state.

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        self.entered_at = monotonic()
        machine.log.info(f'{machine.name} entered {self.name}.')

    def exit(self, machine):
        """
        Actions to perform when exiting the state. Override default behavior with custom exit function

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        machine.log.info(f'{machine.name} left {self.name} after {round(monotonic()-self.entered_at,3)} seconds.')

    def update(self, machine):
        """
        Actions to perform when updating the state.

        Parameters:
        -----------
        machine : StateMachine
            The state machine instance.
        """
        # Update gets looped regularly, so leave logging to the individual state
        pass

class StateMachineOrchestrator:
    """
    A class to manage and coordinate multiple state machines.
    
    Attributes:
    -----------
    state_machines : dict
        A dictionary of state machines managed by the orchestrator
    
    Methods:
    --------
    add_state_machine(name, state_machine):
        Adds a state machine to the orchestrator
    remove_state_machine(name):
        Removes a state machine from the orchestrator
    update():
        Updates all state machines managed by the orchestrator
    run_all():
        Starts all state machines managed by the orchestrator
    stop_all():
        Stops all state machines managed by the orchestrator
    """
    def __init__(self):
        """
        Constructs all the necessary attributes for the state machine orchestrator object.
        """
        self.state_machines = {}

    def add_state_machine(self, name, state_machine):
        """
        Adds a state machine to the orchestrator.

        Parameters:
        -----------
        name : str
            The name of the state machine.
        state_machine : StateMachine
            The state machine to be added.
        """
        self.state_machines[name] = state_machine

    def remove_state_machine(self, name):
        """
        Removes a state machine from the orchestrator.

        Parameters:
        -----------
        name : str
            The name of the state machine to be removed.
        """
        if name in self.state_machines:
            del self.state_machines[name]

    def update(self):
        """
        Updates all state machines managed by the orchestrator.
        """
        for state_machine in self.state_machines.values():
            state_machine.update()

    def run_all(self):
        """
        Starts all state machines managed by the orchestrator.
        """
        for state_machine in self.state_machines.values():
            state_machine.run()

    def stop_all(self):
        """
        Stops all state machines managed by the orchestrator.
        """
        for state_machine in self.state_machines.values():
            state_machine.stop()    
```

### utility.py

```python
import sys

def check_if_microcontroller():
    """
    Determine if the code is running on a microcontroller using CircuitPython.

    Returns:
    bool: True if the code is running on CircuitPython, False otherwise.
    """
    try:
        if sys.implementation.name == 'circuitpython':
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
    return False
```

## temp

### Read_Instructions.py

```python
def read_instructions(filename):
    test = open(filename)
    stuff = test.read()
    stuff = stuff.replace("\r", "").split("\n")
    stuff = stuff[2:]

    cmd = []

    for thing in stuff:
        print(thing)
        cmd.append(thing.split(","))

    return [cmd]


```

### Sidekick_object.py

```python
from machine import Pin
import time
import kinematicsfunctions as kf
import plategen

class Sidekick:
    
    def __init__(self,L1,L2,L3,Ln,Origin,Home,Effector_Location):
        
        # Dimensional Attributes (in cm)
        
        self.L1 = L1
        self.L2 = L2
        self.L3 = L3
        self.Ln = Ln
        
        # Locational Attributes, home is subject to change, right now it is over well a12
        self.home = [90,178]  # there is a `Home` parameter not used in init
        self.origin = Origin
        self.current = Effector_Location #Angular location of stepper
        self.purge = self.loadpurge() #[45.7808, 89.6624]
        self.stepsize = .1125 # 8 microsteps at 0.9 degree motor, 
        self.stepdelay = .0010
        

        # Center Well Lookup Map, saved as platemap1.txt
        
        self.plateinfo = self.loadplate()
        self.alltheta1 = self.plateinfo[0]
        self.alltheta2 = self.plateinfo[1]
        self.wellids = self.plateinfo[2]
        
        
        ########## Hardware attributes, Motor 1 is the top motor, Motor 2 is the bottom motor
        
        ##### Stepper Motor 2 Setup, Bottom Motor
        
        # 1.8 degree steppers, order from top: red,blue,green,black
        
        # Step Pin
        self.motor2 = Pin(10, Pin.OUT)
        self.motor2.value(0)

        # Direction Pin

        self.motor2_d = Pin(9, Pin.OUT)
        self.motor2_d.value(0)

        # Mode Pins

        self.motor2_m0 = Pin(15, Pin.OUT)
        self.motor2_m1 = Pin(14, Pin.OUT)

        # Sleep Pin

        self.motor2_sleep = Pin(16, Pin.OUT)
        self.motor2_sleep.value(0)

        # Setting Mode to 1/8 step, so 0.45 degrees per step on a 1.8 degree stepper

        self.motor2_m0.value(0)
        self.motor2_m1.value(0)
        
        
        ##### Stepper Motor 1 Setup, Top Motor
        # 1.8 degree steppers, order from top: blue,red,green,black

        # Step Pin
        self.motor1 = Pin(1, Pin.OUT)
        self.motor1.value(0)

        # Direction Pin

        self.motor1_d = Pin(0, Pin.OUT)
        self.motor1_d.value(0)

        # Mode Pins

        self.motor1_m0 = Pin(6, Pin.OUT)

        self.motor1_m1 = Pin(5, Pin.OUT)

        # Sleep Pin

        self.motor1_sleep = Pin(7, Pin.OUT)
        self.motor1_sleep.value(0)

        # Setting Mode to 1/8 step, so 0.45 degrees per step

        self.motor1_m0.value(0)
        self.motor1_m1.value(0)
        
        ##### Limit Switch Setup #####
        
        # Front Limit Switch, when activated, lsfront.value = false
        
        self.lsfront = Pin(18, Pin.IN, Pin.PULL_UP)
     
        # Rear Limit Switch, when activated, lsrear.value = false
        
        self.lsrear = Pin(19, Pin.IN, Pin.PULL_UP)
        
        ##### Purge Button #####
        
        self.purgebutton = Pin(20, Pin.IN, Pin.PULL_UP)

        
        ##### Pump Setup #####
        
        # Pump 1
        self.pump1 = Pin(27, Pin.OUT)
        self.pump1.value(0)
        
        # Pump 2
        self.pump2 = Pin(26, Pin.OUT)
        self.pump2.value(0)
        
        # Pump 3
        self.pump3 = Pin(22, Pin.OUT)
        self.pump3.value(0)
        
        # Pump 4
        self.pump4 = Pin(21, Pin.OUT)
        self.pump4.value(0)
    
    # Sidekick Functions
    
    # Plate loading function
    
    @staticmethod
    def loadplate():
        """Take the save text file of well coordinates and read it into memory."""
        
        platefile = open("platemap1.txt","r")
        emptyplate = platefile.read().replace('\r','')
        emptyplate = emptyplate.split("\n")
        platelength = int((len(emptyplate) - 4)/3)
        sectionlength = int((len(emptyplate) - 1)/3)
   
        theta_one = [float(coords) for coords in emptyplate[1:sectionlength] ]
        theta_two = [float(coords) for coords in emptyplate[sectionlength+1:sectionlength*2] ]
        well_ids = emptyplate[(sectionlength*2)+1:len(emptyplate)-1]
        platefile.close()
        return[theta_one,theta_two,well_ids]
    
    # Purge location loading
    
    @staticmethod
    def loadpurge():
        """Take the save text file of purge coordinates and read it into memory."""
        
        purgefile = open("purge1.txt","r")
        purgeloc = purgefile.read()
        purgeloc = purgeloc.split("\n")
        purgeloc = [float(coords) for coords in purgeloc]
        purgefile.close()
        return purgeloc
        
    
    # One step command for the steppers.
    
    def motor1_onestep(self,direction):
        """Command stepper motor 1 to move one step, False is CCW, True is CW"""
        
        self.motor1_d.value(direction) # False is CCW, True is CW
        self.motor1.value(0)
        time.sleep(self.stepdelay)
        self.motor1.value(1)
        time.sleep(self.stepdelay)
        
    def motor2_onestep(self,direction):
        """Command stepper motor 1 to move one step, False is CCW, True is CW"""
        
        self.motor2_d.value(direction) # False is CCW, True is CW
        self.motor2.value(0)
        time.sleep(self.stepdelay)
        self.motor2.value(1)
        time.sleep(self.stepdelay)
    
    # Basic movement function. Moves the steppers to a new angular position, then updates current angular position.

    
    def advangleboth(self,newangle1,newangle2):
        """Move the steppers to a new angular position, update current angular position."""
    
        steps_one = round(abs(newangle1-self.current[0])/self.stepsize)
        final_one = self.current[0] + (round((newangle1-self.current[0])/self.stepsize))*self.stepsize
        steps_two = round(abs(newangle2-self.current[1])/self.stepsize)
        final_two = self.current[1] + (round((newangle2-self.current[1])/self.stepsize))*self.stepsize
        
        if steps_one <= steps_two:
            for x in range(steps_one):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
            for x in range(steps_two-steps_one):
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
            self.current[0] = final_one
            self.current[1] = final_two
        
        if steps_two < steps_one:
            for x in range(steps_two):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
            for x in range(steps_one-steps_two):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
            
            self.current[0] = final_one
            self.current[1] = final_two
    
    # Plate Cycling, allows the user to cycle through the plating process. Good for spotting misalligned plates.
    
    def platecycle(self):
        """Allow the user to cycle through the plating process."""
        
        platecycle = input("Would you like to cycle through the plating process? 'yes' or 'no'  ")

        if platecycle == "yes":
            for well in self.wellids:
                thetas = kf.angle_lookup(well,self.wellids,self.alltheta1,self.alltheta2)
                self.advangleboth(thetas[0], thetas[1])
                print(well, "| ideal thetas:", thetas, "actual thetas:", self.current)
                time.sleep(.4)
                #self.pumpcycle()

            # Return to Starting Position
            self.advangleboth(self.home[0], self.home[1])
    
    # Pump Cycling, places each pump over the centerpoint, mostly for troubleshooting/reliability testing
    
    def pumpcycle(self):
        """Places each pump over the armature centerpoint."""
        
        print(self.current)
        
        center = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
        centerthetas = [self.current[0],self.current[1]]
        
        print(centerthetas)
        
        #loop over the different pump positions
        for position in ["N1","N2", "N3","N4"]:
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,position,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
            time.sleep(.8)
        
        print(self.current)
        self.advangleboth(centerthetas[0], centerthetas[1])
        print(self.current)
    

    ##%% PUMP MOVEMENT METHODS
    
    # Simple move to well function. Moves indicated effector to target well
    
    def movetoXY(self, effector, x, y):
        """Move indicated effector to target well as specified by a cartesian X,Y pair"""
        if effector == "center":
            #Calculates the angular position from given x,y
            thetas = kf.inverse_kinematics(self.L1,self.L2,self.L3,self.origin,[x,y])
            try:
                self.advangleboth(thetas[0], thetas[1])
            except:
                print("Cannot move to position")
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,[x,y],self.origin)
            try:
                self.advangleboth(thetas[0], thetas[1])
            except:
                print("Cannot move to position")
        else:
            print("Indicated pump not recognized")

    def movetowell(self, effector, target_wellid):
        """Move indicated effector to target well."""
        
        if target_wellid == "purge":
            self.movetopurge(effector)
            return
        elif target_wellid not in self.wellids:
            print("The target well is not in the current plate layout")
            return
        
        if effector == "center":
            thetas = kf.angle_lookup(target_wellid,self.wellids,self.alltheta1,self.alltheta2)
            self.advangleboth(thetas[0], thetas[1])
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            wellthetas = kf.angle_lookup(target_wellid,self.wellids,self.alltheta1,self.alltheta2)
            center = kf.forward_kinematics(self.L1,self.L2,self.L3,wellthetas[0],wellthetas[1])
            #print (center)
            #print (pump_label)
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
        else:
            print("Indicated pump not recognized")
    
    # Simple move to theta function. Moves indicated effector to target well.
    
    def movetothetas(self, effector, targetthetas):
        """Move indicated effector to target well."""
        
        if effector == "center":
            self.advangleboth(targetthetas[0], targetthetas[1])
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            center = kf.forward_kinematics(self.L1,self.L2,self.L3,targetthetas[0],targetthetas[1])
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
        else:
            print("Indicated pump not recognized")
            
        
    # Home function, returns effector to set home position
    
    def return_home(self):
        """Return effector to set home position"""
        
        self.advangleboth(self.home[0], self.home[1])
        
    # Moves selected pump to purge location
    
    def movetopurge(self,pumpid):
        """Move selected pump to purge location"""
        
        self.movetothetas(pumpid,self.purge)

    # Allows the user to select a pump, and purge the lines by holding down the purge button.
    def manualpurge(self):
        """Allow the user to select a pump, and purge the lines by holding down the purge button."""
        
        while True:
            ool = 1
            pumpid = input("Which pump would you like to purge? \n Type 'p1', 'p2', 'p3', or 'p4' and hit enter.   ")
            
            if pumpid in {"p1", "p2", "p3", "p4"}:
                self.movetothetas(pumpid,self.purge)
                print("Press and hold the purge button to begin purging line. Release the button to stop.")
                timer = 0
                outerloop = 1
                while outerloop == 1:
                    outerloop = 1
                    if self.purgebutton.value() == 0:
                        timer = 0
                        self.dispense(pumpid,10)
                        #print(self.purgebutton.value())
                        time.sleep(.01)
                    if self.purgebutton.value() == 1:
                        time.sleep(.1)
                        timer=timer+1
                    if self.purgebutton.value() == 1 and timer >= 40:
                        stop = input("Type stop if you want stop. Type anything else if you'd like to continue purging this pump.  ")
                        if stop == "stop" or self.purgebutton.value() == 0:
                            timer = 0
                            outerloop = 0
                        else:
                            timer = 0
            cont = input("Would you like to home another pump? \n Type 'yes' or 'no'   ")
            if cont == "yes":
                ool = 1
            if cont != "yes":
                self.return_home()
                break
        
        
    
    ##%% DISPENSE FUNCTIONS
    
    # Dispenses the commanded amount of liquid from the indicated pump (10 microliter aliquots)
    def dispense(self, pumpLabel, desiredamount):
        """Dispense the commanded amount of liquid from the indicated pump (10 microliter aliquots)."""
        
        actualamount = round(desiredamount/10)*10
        cycles = round(actualamount/10)
        
        # escape if nothing gets pumped
        if cycles == 0:
            return

        print("dispensing", actualamount)

        pumpDictionary = {
            "p1": self.pump1,
            "p2": self.pump2,
            "p3": self.pump3,
            "p4": self.pump4
        }    
        
        if pumpLabel in pumpDictionary: 
            pump = pumpDictionary.get(pumpLabel)
            for i in range(cycles):
                pump.value(1)
                time.sleep(.1)
                #print("energize")
                pump.value(0)
                time.sleep(.1)
                #print("de-energize")
                #print(i)

        elif pumpLabel == "center":
            pass
        else:
            print("Indicated pump label ", pumpLabel, " is not recognized")

    # Finds the endpoints, run first whenever waking the machine!
    
    def initialize(self):
        """Find the endpoints of armature travel."""
        
        self.motor2_sleep.value(1)
        # Calibrates Motor 1, (Upper Motor)
        
        while self.lsfront.value() != 0:
            self.motor1_onestep(1)
            time.sleep(self.stepdelay*3)
        if self.lsfront.value() == 0:
            print("Front limit reached")
            self.current[0] = 0
        
        # Calibrates Motor 2, (Lower Motor)
        self.motor2_sleep.value(0)
        
        while self.lsrear.value() != 0:
            self.motor1_onestep(0)
            self.current[0] = self.current[0] + self.stepsize
            self.motor2_onestep(0)
            time.sleep(self.stepdelay*3)
        if self.lsrear.value() == 0:
                print("Rear limit reached")
                self.current[1] = 180
        
        self.return_home()
        
    # Hardware Check, checks if everything is working properly, used to validate wiring during build.
    
    def hardwarecheck(self):
        """Hardware Check, check if everything is working properly, use to validate wiring during build."""
    
        self.motor2_sleep.value(1)
        # Calibrates Motor 1, (Upper Motor)
        print("Testing top motor. Armature movement should be clockwise, moving to front of Sidekick")
        while self.lsfront.value() != 0:
            self.motor1_onestep(1)
            time.sleep(self.stepdelay*3)
        if self.lsfront.value() == 0:
            print("Front limit switch triggered")
            self.current[0] = 0
        
        # Calibrates Motor 2, (Lower Motor)
        self.motor2_sleep.value(0)
        
        print("Testing lower motor. Armature movement should be counterclockwise, moving to rear of Sidekick")
        while self.lsrear.value() != 0:
            self.motor1_onestep(0)
            self.current[0] = self.current[0] + self.stepsize
            self.motor2_onestep(0)
            time.sleep(self.stepdelay*3)
        if self.lsrear.value() == 0:
                print("Rear limit switch triggered")
                self.current[1] = 180
        
        self.return_home()
        
        print("testing pump 1 (closest to front). You should hear clicking as the pump energizes.")
        
        self.dispense("p1", 100)
        print("testing pump 2.")
        self.dispense("p2", 100)
        print("testing pump 3.")
        self.dispense("p3", 100)
        print("testing pump 4.")
        self.dispense("p4", 100)
        
        print("testing purge button. Click the purge button, then release it. \nThe Sidekick will output whether it detects that the button is held or released.")
        
        time.sleep(5)
        
        ot = 1
        btest = 1
        while ot == 1:
            if self.purgebutton.value() == 0:
                while btest == 1:
                    if self.purgebutton.value() == 0:
                        print("purge button pressed")
                        time.sleep(.1)
                    if self.purgebutton.value() == 1:
                        print("purge button released")
                        btest =0
                        ot = 0
                     

        print("Hardware check complete. If any components did not behave as described, please troubleshoot wiring")
        
    
    # Releases both motors
    
    def release(self):
        """Release both motors"""

        self.motor1_sleep.value(1)
        self.motor2_sleep.value(1)
    
    # Wakes both motors
    
    def wake(self):
        """Wake both motors"""
        
        self.motor1_sleep.value(0)
        self.motor2_sleep.value(0)
        self.initialize()

    
    def current_xy(self):
        """returns the current [x, y] position as a list"""
        return kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
    
    def print_angular_position(self):
        """prints the current [theta_1, theta_2] position as a list"""
        print(self.current[0],self.current[1])
        
    def print_current_xy(self):
        """returns the current [x, y] position as a list"""
        print(kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1]))


    # Allows the user to move the effector freely, then prints position.
    
    def freemove(self):
        """Allow the user to move the effector freely, then print position."""
        
        nearestwell = input("enter closest well  ")
        self.movetowell("center", nearestwell) 
        while True:
            direction = input("enter direction with w,a,s,d, the hit enter. If finished, enter 'finished'  ")
            if direction == "s":
                newangles = kf.down(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "w":
                newangles = kf.up(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "a":
                newangles = kf.left(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "d":
                newangles = kf.right(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "finished":
                position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                print("Freemove ended. Current angles are", self.current, "Current location is", position)
                break
            
    def purgeset(self):
        """Set the location of the purge vessel"""

        nearestwell = input("enter closest well to purge location  ")
        thetas =  kf.angle_lookup(nearestwell,self.wellids,self.alltheta1,self.alltheta2)
        self.advangleboth(thetas[0], thetas[1])
        while True:
            direction = input("enter direction with w,a,s,d, the hit enter.\n If centered over the purge location, enter 'finished'  ")
            if direction == "s":
                newangles = kf.down(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "w":
                newangles = kf.up(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "a":
                newangles = kf.left(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "d":
                newangles = kf.right(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "finished":
                position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                print("Freemove ended. Current angles are", self.current, "Current location is", position)
                break
        file = open("purge1.txt", "w")
        file.write(str(self.current[0]) + "\n")
        file.write(str(self.current[1]))
        file.close()
        self.return_home()

    # Regenerates the plate map. Use if plating for the first time, or if using new plates.
    def remap(self):
        """Regenerate the plate map. Use if plating for the first time, or if using new plates."""
        
        
        while True:
            calibrate = input("Calibrate? Type 'yes' to continue, or 'no' to stop  ")
            if calibrate == "no":
                break
            if calibrate == "yes":
                
                
                calcorners = ['a1','a12','h1','h12']
                calcorner_pos = []
                
                for x in range(4):
                    thetas =  kf.angle_lookup(calcorners[x],self.wellids,self.alltheta1,self.alltheta2)
                    if x == 0:
                        print("Center over the top left well")
                    if x == 1:
                        print("Center over the top right well")
                    if x == 2:
                        print("Center over the bottom left well")
                    if x == 3:
                        print("Center over the bottom right well")
                    
                    self.advangleboth(thetas[0], thetas[1])
                    
                    while True:
                        direction = input("enter direction with w,a,s,d, the hit enter. If finished, enter 'calibrate'  ")
                        if direction == "s":
                            newangles = kf.down(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "w":
                            newangles = kf.up(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "a":
                            newangles = kf.left(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "d":
                            newangles = kf.right(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "calibrate":
                            position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                            print("Calibration complete! Corrected angles are", self.current, "Corrected location is", position)
                            calcorner_pos.append(position)
                            break
                results = plategen.remap_plate(calcorner_pos[0],calcorner_pos[1],calcorner_pos[2],calcorner_pos[3],self.L1,self.L2,self.L3,self.origin)
                print(results[0])
                print(results[1])
                print(results[2])
                file = open("platemap1.txt", "w")
                file.write("theta_one \n")
                for coord in results[0]:
                    file.write(str(coord) + "\n")
                file.write("theta_two \n")
                for coord in results[1]:
                    file.write(str(coord) + "\n")
                file.write("well_ids \n")
                for coord in results[2]:
                    file.write(coord + "\n")
                file.close()
                self.plateinfo = self.loadplate()
                self.alltheta1 = self.plateinfo[0]
                self.alltheta2 = self.plateinfo[1]
                self.wellids = self.plateinfo[2]
                self.return_home()
    
    # Reads a CSV file and turns it into commands.
    
    @staticmethod
    def read_instructions(filename):
        """Read a CSV file and turn it into commands."""
        
        test = open(filename)
        stuff = test.read()
        stuff = stuff.replace("\r", "").split("\n")
        stuff = stuff[1:]

        cmd = [stuff[i].split(",") for i in range(len(stuff) - 1)]

        #print(cmd)

        return cmd
    
    # Takes a CSV file of instructions, and plates them.
    
    def execute_protocol(self, filename="saved_protocol.csv"):
        """Take a CSV file of instructions, and plate them."""

        commands = self.read_instructions(filename)
        print(commands)
        for cmd in commands:
            pumpid, targetwell, desiredamount = cmd[0:3]
            #print(targetwell)
            #print(pumpid)
            #print(desiredamount)
            
            self.movetowell(pumpid,targetwell)
            self.dispense(pumpid, float(desiredamount))


                
#alpha = Sidekick(7,3,10,0.5,[0,0],[90,178],[119.484,171.701]) # This is the template of the default Sidekick.


```

### all-in-one.md

```markdown
## .

### Read_Instructions.py

```python
def read_instructions(filename):
    test = open(filename)
    stuff = test.read()
    stuff = stuff.replace("\r", "").split("\n")
    stuff = stuff[2:]

    cmd = []

    for thing in stuff:
        print(thing)
        cmd.append(thing.split(","))

    return [cmd]


```

### Sidekick_object.py

```python
from machine import Pin
import time
import kinematicsfunctions as kf
import plategen

class Sidekick:
    
    def __init__(self,L1,L2,L3,Ln,Origin,Home,Effector_Location):
        
        # Dimensional Attributes (in cm)
        
        self.L1 = L1
        self.L2 = L2
        self.L3 = L3
        self.Ln = Ln
        
        # Locational Attributes, home is subject to change, right now it is over well a12
        self.home = [90,178]  # there is a `Home` parameter not used in init
        self.origin = Origin
        self.current = Effector_Location #Angular location of stepper
        self.purge = self.loadpurge() #[45.7808, 89.6624]
        self.stepsize = .1125 # 8 microsteps at 0.9 degree motor, 
        self.stepdelay = .0010
        

        # Center Well Lookup Map, saved as platemap1.txt
        
        self.plateinfo = self.loadplate()
        self.alltheta1 = self.plateinfo[0]
        self.alltheta2 = self.plateinfo[1]
        self.wellids = self.plateinfo[2]
        
        
        ########## Hardware attributes, Motor 1 is the top motor, Motor 2 is the bottom motor
        
        ##### Stepper Motor 2 Setup, Bottom Motor
        
        # 1.8 degree steppers, order from top: red,blue,green,black
        
        # Step Pin
        self.motor2 = Pin(10, Pin.OUT)
        self.motor2.value(0)

        # Direction Pin

        self.motor2_d = Pin(9, Pin.OUT)
        self.motor2_d.value(0)

        # Mode Pins

        self.motor2_m0 = Pin(15, Pin.OUT)
        self.motor2_m1 = Pin(14, Pin.OUT)

        # Sleep Pin

        self.motor2_sleep = Pin(16, Pin.OUT)
        self.motor2_sleep.value(0)

        # Setting Mode to 1/8 step, so 0.45 degrees per step on a 1.8 degree stepper

        self.motor2_m0.value(0)
        self.motor2_m1.value(0)
        
        
        ##### Stepper Motor 1 Setup, Top Motor
        # 1.8 degree steppers, order from top: blue,red,green,black

        # Step Pin
        self.motor1 = Pin(1, Pin.OUT)
        self.motor1.value(0)

        # Direction Pin

        self.motor1_d = Pin(0, Pin.OUT)
        self.motor1_d.value(0)

        # Mode Pins

        self.motor1_m0 = Pin(6, Pin.OUT)

        self.motor1_m1 = Pin(5, Pin.OUT)

        # Sleep Pin

        self.motor1_sleep = Pin(7, Pin.OUT)
        self.motor1_sleep.value(0)

        # Setting Mode to 1/8 step, so 0.45 degrees per step

        self.motor1_m0.value(0)
        self.motor1_m1.value(0)
        
        ##### Limit Switch Setup #####
        
        # Front Limit Switch, when activated, lsfront.value = false
        
        self.lsfront = Pin(18, Pin.IN, Pin.PULL_UP)
     
        # Rear Limit Switch, when activated, lsrear.value = false
        
        self.lsrear = Pin(19, Pin.IN, Pin.PULL_UP)
        
        ##### Purge Button #####
        
        self.purgebutton = Pin(20, Pin.IN, Pin.PULL_UP)

        
        ##### Pump Setup #####
        
        # Pump 1
        self.pump1 = Pin(27, Pin.OUT)
        self.pump1.value(0)
        
        # Pump 2
        self.pump2 = Pin(26, Pin.OUT)
        self.pump2.value(0)
        
        # Pump 3
        self.pump3 = Pin(22, Pin.OUT)
        self.pump3.value(0)
        
        # Pump 4
        self.pump4 = Pin(21, Pin.OUT)
        self.pump4.value(0)
    
    # Sidekick Functions
    
    # Plate loading function
    
    @staticmethod
    def loadplate():
        """Take the save text file of well coordinates and read it into memory."""
        
        platefile = open("platemap1.txt","r")
        emptyplate = platefile.read().replace('\r','')
        emptyplate = emptyplate.split("\n")
        platelength = int((len(emptyplate) - 4)/3)
        sectionlength = int((len(emptyplate) - 1)/3)
   
        theta_one = [float(coords) for coords in emptyplate[1:sectionlength] ]
        theta_two = [float(coords) for coords in emptyplate[sectionlength+1:sectionlength*2] ]
        well_ids = emptyplate[(sectionlength*2)+1:len(emptyplate)-1]
        platefile.close()
        return[theta_one,theta_two,well_ids]
    
    # Purge location loading
    
    @staticmethod
    def loadpurge():
        """Take the save text file of purge coordinates and read it into memory."""
        
        purgefile = open("purge1.txt","r")
        purgeloc = purgefile.read()
        purgeloc = purgeloc.split("\n")
        purgeloc = [float(coords) for coords in purgeloc]
        purgefile.close()
        return purgeloc
        
    
    # One step command for the steppers.
    
    def motor1_onestep(self,direction):
        """Command stepper motor 1 to move one step, False is CCW, True is CW"""
        
        self.motor1_d.value(direction) # False is CCW, True is CW
        self.motor1.value(0)
        time.sleep(self.stepdelay)
        self.motor1.value(1)
        time.sleep(self.stepdelay)
        
    def motor2_onestep(self,direction):
        """Command stepper motor 1 to move one step, False is CCW, True is CW"""
        
        self.motor2_d.value(direction) # False is CCW, True is CW
        self.motor2.value(0)
        time.sleep(self.stepdelay)
        self.motor2.value(1)
        time.sleep(self.stepdelay)
    
    # Basic movement function. Moves the steppers to a new angular position, then updates current angular position.

    
    def advangleboth(self,newangle1,newangle2):
        """Move the steppers to a new angular position, update current angular position."""
    
        steps_one = round(abs(newangle1-self.current[0])/self.stepsize)
        final_one = self.current[0] + (round((newangle1-self.current[0])/self.stepsize))*self.stepsize
        steps_two = round(abs(newangle2-self.current[1])/self.stepsize)
        final_two = self.current[1] + (round((newangle2-self.current[1])/self.stepsize))*self.stepsize
        
        if steps_one <= steps_two:
            for x in range(steps_one):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
            for x in range(steps_two-steps_one):
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
            self.current[0] = final_one
            self.current[1] = final_two
        
        if steps_two < steps_one:
            for x in range(steps_two):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
            for x in range(steps_one-steps_two):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
            
            self.current[0] = final_one
            self.current[1] = final_two
    
    # Plate Cycling, allows the user to cycle through the plating process. Good for spotting misalligned plates.
    
    def platecycle(self):
        """Allow the user to cycle through the plating process."""
        
        platecycle = input("Would you like to cycle through the plating process? 'yes' or 'no'  ")

        if platecycle == "yes":
            for well in self.wellids:
                thetas = kf.angle_lookup(well,self.wellids,self.alltheta1,self.alltheta2)
                self.advangleboth(thetas[0], thetas[1])
                print(well, "| ideal thetas:", thetas, "actual thetas:", self.current)
                time.sleep(.4)
                #self.pumpcycle()

            # Return to Starting Position
            self.advangleboth(self.home[0], self.home[1])
    
    # Pump Cycling, places each pump over the centerpoint, mostly for troubleshooting/reliability testing
    
    def pumpcycle(self):
        """Places each pump over the armature centerpoint."""
        
        print(self.current)
        
        center = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
        centerthetas = [self.current[0],self.current[1]]
        
        print(centerthetas)
        
        #loop over the different pump positions
        for position in ["N1","N2", "N3","N4"]:
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,position,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
            time.sleep(.8)
        
        print(self.current)
        self.advangleboth(centerthetas[0], centerthetas[1])
        print(self.current)
    

    ##%% PUMP MOVEMENT METHODS
    
    # Simple move to well function. Moves indicated effector to target well
    
    def movetoXY(self, effector, x, y):
        """Move indicated effector to target well as specified by a cartesian X,Y pair"""
        if effector == "center":
            #Calculates the angular position from given x,y
            thetas = kf.inverse_kinematics(self.L1,self.L2,self.L3,self.origin,[x,y])
            try:
                self.advangleboth(thetas[0], thetas[1])
            except:
                print("Cannot move to position")
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,[x,y],self.origin)
            try:
                self.advangleboth(thetas[0], thetas[1])
            except:
                print("Cannot move to position")
        else:
            print("Indicated pump not recognized")

    def movetowell(self, effector, target_wellid):
        """Move indicated effector to target well."""
        
        if target_wellid == "purge":
            self.movetopurge(effector)
            return
        elif target_wellid not in self.wellids:
            print("The target well is not in the current plate layout")
            return
        
        if effector == "center":
            thetas = kf.angle_lookup(target_wellid,self.wellids,self.alltheta1,self.alltheta2)
            self.advangleboth(thetas[0], thetas[1])
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            wellthetas = kf.angle_lookup(target_wellid,self.wellids,self.alltheta1,self.alltheta2)
            center = kf.forward_kinematics(self.L1,self.L2,self.L3,wellthetas[0],wellthetas[1])
            #print (center)
            #print (pump_label)
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
        else:
            print("Indicated pump not recognized")
    
    # Simple move to theta function. Moves indicated effector to target well.
    
    def movetothetas(self, effector, targetthetas):
        """Move indicated effector to target well."""
        
        if effector == "center":
            self.advangleboth(targetthetas[0], targetthetas[1])
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            center = kf.forward_kinematics(self.L1,self.L2,self.L3,targetthetas[0],targetthetas[1])
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
        else:
            print("Indicated pump not recognized")
            
        
    # Home function, returns effector to set home position
    
    def return_home(self):
        """Return effector to set home position"""
        
        self.advangleboth(self.home[0], self.home[1])
        
    # Moves selected pump to purge location
    
    def movetopurge(self,pumpid):
        """Move selected pump to purge location"""
        
        self.movetothetas(pumpid,self.purge)

    # Allows the user to select a pump, and purge the lines by holding down the purge button.
    def manualpurge(self):
        """Allow the user to select a pump, and purge the lines by holding down the purge button."""
        
        while True:
            ool = 1
            pumpid = input("Which pump would you like to purge? \n Type 'p1', 'p2', 'p3', or 'p4' and hit enter.   ")
            
            if pumpid in {"p1", "p2", "p3", "p4"}:
                self.movetothetas(pumpid,self.purge)
                print("Press and hold the purge button to begin purging line. Release the button to stop.")
                timer = 0
                outerloop = 1
                while outerloop == 1:
                    outerloop = 1
                    if self.purgebutton.value() == 0:
                        timer = 0
                        self.dispense(pumpid,10)
                        #print(self.purgebutton.value())
                        time.sleep(.01)
                    if self.purgebutton.value() == 1:
                        time.sleep(.1)
                        timer=timer+1
                    if self.purgebutton.value() == 1 and timer >= 40:
                        stop = input("Type stop if you want stop. Type anything else if you'd like to continue purging this pump.  ")
                        if stop == "stop" or self.purgebutton.value() == 0:
                            timer = 0
                            outerloop = 0
                        else:
                            timer = 0
            cont = input("Would you like to home another pump? \n Type 'yes' or 'no'   ")
            if cont == "yes":
                ool = 1
            if cont != "yes":
                self.return_home()
                break
        
        
    
    ##%% DISPENSE FUNCTIONS
    
    # Dispenses the commanded amount of liquid from the indicated pump (10 microliter aliquots)
    def dispense(self, pumpLabel, desiredamount):
        """Dispense the commanded amount of liquid from the indicated pump (10 microliter aliquots)."""
        
        actualamount = round(desiredamount/10)*10
        cycles = round(actualamount/10)
        
        # escape if nothing gets pumped
        if cycles == 0:
            return

        print("dispensing", actualamount)

        pumpDictionary = {
            "p1": self.pump1,
            "p2": self.pump2,
            "p3": self.pump3,
            "p4": self.pump4
        }    
        
        if pumpLabel in pumpDictionary: 
            pump = pumpDictionary.get(pumpLabel)
            for i in range(cycles):
                pump.value(1)
                time.sleep(.1)
                #print("energize")
                pump.value(0)
                time.sleep(.1)
                #print("de-energize")
                #print(i)

        elif pumpLabel == "center":
            pass
        else:
            print("Indicated pump label ", pumpLabel, " is not recognized")

    # Finds the endpoints, run first whenever waking the machine!
    
    def initialize(self):
        """Find the endpoints of armature travel."""
        
        self.motor2_sleep.value(1)
        # Calibrates Motor 1, (Upper Motor)
        
        while self.lsfront.value() != 0:
            self.motor1_onestep(1)
            time.sleep(self.stepdelay*3)
        if self.lsfront.value() == 0:
            print("Front limit reached")
            self.current[0] = 0
        
        # Calibrates Motor 2, (Lower Motor)
        self.motor2_sleep.value(0)
        
        while self.lsrear.value() != 0:
            self.motor1_onestep(0)
            self.current[0] = self.current[0] + self.stepsize
            self.motor2_onestep(0)
            time.sleep(self.stepdelay*3)
        if self.lsrear.value() == 0:
                print("Rear limit reached")
                self.current[1] = 180
        
        self.return_home()
        
    # Hardware Check, checks if everything is working properly, used to validate wiring during build.
    
    def hardwarecheck(self):
        """Hardware Check, check if everything is working properly, use to validate wiring during build."""
    
        self.motor2_sleep.value(1)
        # Calibrates Motor 1, (Upper Motor)
        print("Testing top motor. Armature movement should be clockwise, moving to front of Sidekick")
        while self.lsfront.value() != 0:
            self.motor1_onestep(1)
            time.sleep(self.stepdelay*3)
        if self.lsfront.value() == 0:
            print("Front limit switch triggered")
            self.current[0] = 0
        
        # Calibrates Motor 2, (Lower Motor)
        self.motor2_sleep.value(0)
        
        print("Testing lower motor. Armature movement should be counterclockwise, moving to rear of Sidekick")
        while self.lsrear.value() != 0:
            self.motor1_onestep(0)
            self.current[0] = self.current[0] + self.stepsize
            self.motor2_onestep(0)
            time.sleep(self.stepdelay*3)
        if self.lsrear.value() == 0:
                print("Rear limit switch triggered")
                self.current[1] = 180
        
        self.return_home()
        
        print("testing pump 1 (closest to front). You should hear clicking as the pump energizes.")
        
        self.dispense("p1", 100)
        print("testing pump 2.")
        self.dispense("p2", 100)
        print("testing pump 3.")
        self.dispense("p3", 100)
        print("testing pump 4.")
        self.dispense("p4", 100)
        
        print("testing purge button. Click the purge button, then release it. \nThe Sidekick will output whether it detects that the button is held or released.")
        
        time.sleep(5)
        
        ot = 1
        btest = 1
        while ot == 1:
            if self.purgebutton.value() == 0:
                while btest == 1:
                    if self.purgebutton.value() == 0:
                        print("purge button pressed")
                        time.sleep(.1)
                    if self.purgebutton.value() == 1:
                        print("purge button released")
                        btest =0
                        ot = 0
                     

        print("Hardware check complete. If any components did not behave as described, please troubleshoot wiring")
        
    
    # Releases both motors
    
    def release(self):
        """Release both motors"""

        self.motor1_sleep.value(1)
        self.motor2_sleep.value(1)
    
    # Wakes both motors
    
    def wake(self):
        """Wake both motors"""
        
        self.motor1_sleep.value(0)
        self.motor2_sleep.value(0)
        self.initialize()

    
    def current_xy(self):
        """returns the current [x, y] position as a list"""
        return kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
    
    def print_angular_position(self):
        """prints the current [theta_1, theta_2] position as a list"""
        print(self.current[0],self.current[1])
        
    def print_current_xy(self):
        """returns the current [x, y] position as a list"""
        print(kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1]))


    # Allows the user to move the effector freely, then prints position.
    
    def freemove(self):
        """Allow the user to move the effector freely, then print position."""
        
        nearestwell = input("enter closest well  ")
        self.movetowell("center", nearestwell) 
        while True:
            direction = input("enter direction with w,a,s,d, the hit enter. If finished, enter 'finished'  ")
            if direction == "s":
                newangles = kf.down(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "w":
                newangles = kf.up(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "a":
                newangles = kf.left(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "d":
                newangles = kf.right(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "finished":
                position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                print("Freemove ended. Current angles are", self.current, "Current location is", position)
                break
            
    def purgeset(self):
        """Set the location of the purge vessel"""

        nearestwell = input("enter closest well to purge location  ")
        thetas =  kf.angle_lookup(nearestwell,self.wellids,self.alltheta1,self.alltheta2)
        self.advangleboth(thetas[0], thetas[1])
        while True:
            direction = input("enter direction with w,a,s,d, the hit enter.\n If centered over the purge location, enter 'finished'  ")
            if direction == "s":
                newangles = kf.down(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "w":
                newangles = kf.up(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "a":
                newangles = kf.left(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "d":
                newangles = kf.right(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "finished":
                position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                print("Freemove ended. Current angles are", self.current, "Current location is", position)
                break
        file = open("purge1.txt", "w")
        file.write(str(self.current[0]) + "\n")
        file.write(str(self.current[1]))
        file.close()
        self.return_home()

    # Regenerates the plate map. Use if plating for the first time, or if using new plates.
    def remap(self):
        """Regenerate the plate map. Use if plating for the first time, or if using new plates."""
        
        
        while True:
            calibrate = input("Calibrate? Type 'yes' to continue, or 'no' to stop  ")
            if calibrate == "no":
                break
            if calibrate == "yes":
                
                
                calcorners = ['a1','a12','h1','h12']
                calcorner_pos = []
                
                for x in range(4):
                    thetas =  kf.angle_lookup(calcorners[x],self.wellids,self.alltheta1,self.alltheta2)
                    if x == 0:
                        print("Center over the top left well")
                    if x == 1:
                        print("Center over the top right well")
                    if x == 2:
                        print("Center over the bottom left well")
                    if x == 3:
                        print("Center over the bottom right well")
                    
                    self.advangleboth(thetas[0], thetas[1])
                    
                    while True:
                        direction = input("enter direction with w,a,s,d, the hit enter. If finished, enter 'calibrate'  ")
                        if direction == "s":
                            newangles = kf.down(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "w":
                            newangles = kf.up(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "a":
                            newangles = kf.left(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "d":
                            newangles = kf.right(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "calibrate":
                            position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                            print("Calibration complete! Corrected angles are", self.current, "Corrected location is", position)
                            calcorner_pos.append(position)
                            break
                results = plategen.remap_plate(calcorner_pos[0],calcorner_pos[1],calcorner_pos[2],calcorner_pos[3],self.L1,self.L2,self.L3,self.origin)
                print(results[0])
                print(results[1])
                print(results[2])
                file = open("platemap1.txt", "w")
                file.write("theta_one \n")
                for coord in results[0]:
                    file.write(str(coord) + "\n")
                file.write("theta_two \n")
                for coord in results[1]:
                    file.write(str(coord) + "\n")
                file.write("well_ids \n")
                for coord in results[2]:
                    file.write(coord + "\n")
                file.close()
                self.plateinfo = self.loadplate()
                self.alltheta1 = self.plateinfo[0]
                self.alltheta2 = self.plateinfo[1]
                self.wellids = self.plateinfo[2]
                self.return_home()
    
    # Reads a CSV file and turns it into commands.
    
    @staticmethod
    def read_instructions(filename):
        """Read a CSV file and turn it into commands."""
        
        test = open(filename)
        stuff = test.read()
        stuff = stuff.replace("\r", "").split("\n")
        stuff = stuff[1:]

        cmd = [stuff[i].split(",") for i in range(len(stuff) - 1)]

        #print(cmd)

        return cmd
    
    # Takes a CSV file of instructions, and plates them.
    
    def execute_protocol(self, filename="saved_protocol.csv"):
        """Take a CSV file of instructions, and plate them."""

        commands = self.read_instructions(filename)
        print(commands)
        for cmd in commands:
            pumpid, targetwell, desiredamount = cmd[0:3]
            #print(targetwell)
            #print(pumpid)
            #print(desiredamount)
            
            self.movetowell(pumpid,targetwell)
            self.dispense(pumpid, float(desiredamount))


                
#alpha = Sidekick(7,3,10,0.5,[0,0],[90,178],[119.484,171.701]) # This is the template of the default Sidekick.


```

### all-in-one.md

```markdown
## .

### Read_Instructions.py

```python
def read_instructions(filename):
    test = open(filename)
    stuff = test.read()
    stuff = stuff.replace("\r", "").split("\n")
    stuff = stuff[2:]

    cmd = []

    for thing in stuff:
        print(thing)
        cmd.append(thing.split(","))

    return [cmd]


```

### Sidekick_object.py

```python
from machine import Pin
import time
import kinematicsfunctions as kf
import plategen

class Sidekick:
    
    def __init__(self,L1,L2,L3,Ln,Origin,Home,Effector_Location):
        
        # Dimensional Attributes (in cm)
        
        self.L1 = L1
        self.L2 = L2
        self.L3 = L3
        self.Ln = Ln
        
        # Locational Attributes, home is subject to change, right now it is over well a12
        self.home = [90,178]  # there is a `Home` parameter not used in init
        self.origin = Origin
        self.current = Effector_Location #Angular location of stepper
        self.purge = self.loadpurge() #[45.7808, 89.6624]
        self.stepsize = .1125 # 8 microsteps at 0.9 degree motor, 
        self.stepdelay = .0010
        

        # Center Well Lookup Map, saved as platemap1.txt
        
        self.plateinfo = self.loadplate()
        self.alltheta1 = self.plateinfo[0]
        self.alltheta2 = self.plateinfo[1]
        self.wellids = self.plateinfo[2]
        
        
        ########## Hardware attributes, Motor 1 is the top motor, Motor 2 is the bottom motor
        
        ##### Stepper Motor 2 Setup, Bottom Motor
        
        # 1.8 degree steppers, order from top: red,blue,green,black
        
        # Step Pin
        self.motor2 = Pin(10, Pin.OUT)
        self.motor2.value(0)

        # Direction Pin

        self.motor2_d = Pin(9, Pin.OUT)
        self.motor2_d.value(0)

        # Mode Pins

        self.motor2_m0 = Pin(15, Pin.OUT)
        self.motor2_m1 = Pin(14, Pin.OUT)

        # Sleep Pin

        self.motor2_sleep = Pin(16, Pin.OUT)
        self.motor2_sleep.value(0)

        # Setting Mode to 1/8 step, so 0.45 degrees per step on a 1.8 degree stepper

        self.motor2_m0.value(0)
        self.motor2_m1.value(0)
        
        
        ##### Stepper Motor 1 Setup, Top Motor
        # 1.8 degree steppers, order from top: blue,red,green,black

        # Step Pin
        self.motor1 = Pin(1, Pin.OUT)
        self.motor1.value(0)

        # Direction Pin

        self.motor1_d = Pin(0, Pin.OUT)
        self.motor1_d.value(0)

        # Mode Pins

        self.motor1_m0 = Pin(6, Pin.OUT)

        self.motor1_m1 = Pin(5, Pin.OUT)

        # Sleep Pin

        self.motor1_sleep = Pin(7, Pin.OUT)
        self.motor1_sleep.value(0)

        # Setting Mode to 1/8 step, so 0.45 degrees per step

        self.motor1_m0.value(0)
        self.motor1_m1.value(0)
        
        ##### Limit Switch Setup #####
        
        # Front Limit Switch, when activated, lsfront.value = false
        
        self.lsfront = Pin(18, Pin.IN, Pin.PULL_UP)
     
        # Rear Limit Switch, when activated, lsrear.value = false
        
        self.lsrear = Pin(19, Pin.IN, Pin.PULL_UP)
        
        ##### Purge Button #####
        
        self.purgebutton = Pin(20, Pin.IN, Pin.PULL_UP)

        
        ##### Pump Setup #####
        
        # Pump 1
        self.pump1 = Pin(27, Pin.OUT)
        self.pump1.value(0)
        
        # Pump 2
        self.pump2 = Pin(26, Pin.OUT)
        self.pump2.value(0)
        
        # Pump 3
        self.pump3 = Pin(22, Pin.OUT)
        self.pump3.value(0)
        
        # Pump 4
        self.pump4 = Pin(21, Pin.OUT)
        self.pump4.value(0)
    
    # Sidekick Functions
    
    # Plate loading function
    
    @staticmethod
    def loadplate():
        """Take the save text file of well coordinates and read it into memory."""
        
        platefile = open("platemap1.txt","r")
        emptyplate = platefile.read().replace('\r','')
        emptyplate = emptyplate.split("\n")
        platelength = int((len(emptyplate) - 4)/3)
        sectionlength = int((len(emptyplate) - 1)/3)
   
        theta_one = [float(coords) for coords in emptyplate[1:sectionlength] ]
        theta_two = [float(coords) for coords in emptyplate[sectionlength+1:sectionlength*2] ]
        well_ids = emptyplate[(sectionlength*2)+1:len(emptyplate)-1]
        platefile.close()
        return[theta_one,theta_two,well_ids]
    
    # Purge location loading
    
    @staticmethod
    def loadpurge():
        """Take the save text file of purge coordinates and read it into memory."""
        
        purgefile = open("purge1.txt","r")
        purgeloc = purgefile.read()
        purgeloc = purgeloc.split("\n")
        purgeloc = [float(coords) for coords in purgeloc]
        purgefile.close()
        return purgeloc
        
    
    # One step command for the steppers.
    
    def motor1_onestep(self,direction):
        """Command stepper motor 1 to move one step, False is CCW, True is CW"""
        
        self.motor1_d.value(direction) # False is CCW, True is CW
        self.motor1.value(0)
        time.sleep(self.stepdelay)
        self.motor1.value(1)
        time.sleep(self.stepdelay)
        
    def motor2_onestep(self,direction):
        """Command stepper motor 1 to move one step, False is CCW, True is CW"""
        
        self.motor2_d.value(direction) # False is CCW, True is CW
        self.motor2.value(0)
        time.sleep(self.stepdelay)
        self.motor2.value(1)
        time.sleep(self.stepdelay)
    
    # Basic movement function. Moves the steppers to a new angular position, then updates current angular position.

    
    def advangleboth(self,newangle1,newangle2):
        """Move the steppers to a new angular position, update current angular position."""
    
        steps_one = round(abs(newangle1-self.current[0])/self.stepsize)
        final_one = self.current[0] + (round((newangle1-self.current[0])/self.stepsize))*self.stepsize
        steps_two = round(abs(newangle2-self.current[1])/self.stepsize)
        final_two = self.current[1] + (round((newangle2-self.current[1])/self.stepsize))*self.stepsize
        
        if steps_one <= steps_two:
            for x in range(steps_one):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
            for x in range(steps_two-steps_one):
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
            self.current[0] = final_one
            self.current[1] = final_two
        
        if steps_two < steps_one:
            for x in range(steps_two):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                if self.current[1] <= newangle2:
                    self.motor2_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
                else:
                    self.motor2_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay)
            for x in range(steps_one-steps_two):
                if self.current[0] <= newangle1:
                    self.motor1_onestep(0) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
                else:
                    self.motor1_onestep(1) #style=stepper.INTERLEAVE
                    time.sleep(self.stepdelay*2)
            
            self.current[0] = final_one
            self.current[1] = final_two
    
    # Plate Cycling, allows the user to cycle through the plating process. Good for spotting misalligned plates.
    
    def platecycle(self):
        """Allow the user to cycle through the plating process."""
        
        platecycle = input("Would you like to cycle through the plating process? 'yes' or 'no'  ")

        if platecycle == "yes":
            for well in self.wellids:
                thetas = kf.angle_lookup(well,self.wellids,self.alltheta1,self.alltheta2)
                self.advangleboth(thetas[0], thetas[1])
                print(well, "| ideal thetas:", thetas, "actual thetas:", self.current)
                time.sleep(.4)
                #self.pumpcycle()

            # Return to Starting Position
            self.advangleboth(self.home[0], self.home[1])
    
    # Pump Cycling, places each pump over the centerpoint, mostly for troubleshooting/reliability testing
    
    def pumpcycle(self):
        """Places each pump over the armature centerpoint."""
        
        print(self.current)
        
        center = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
        centerthetas = [self.current[0],self.current[1]]
        
        print(centerthetas)
        
        #loop over the different pump positions
        for position in ["N1","N2", "N3","N4"]:
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,position,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
            time.sleep(.8)
        
        print(self.current)
        self.advangleboth(centerthetas[0], centerthetas[1])
        print(self.current)
    

    ##%% PUMP MOVEMENT METHODS
    
    # Simple move to well function. Moves indicated effector to target well
    
    def movetoXY(self, effector, x, y):
        """Move indicated effector to target well as specified by a cartesian X,Y pair"""
        if effector == "center":
            #Calculates the angular position from given x,y
            thetas = kf.inverse_kinematics(self.L1,self.L2,self.L3,self.origin,[x,y])
            try:
                self.advangleboth(thetas[0], thetas[1])
            except:
                print("Cannot move to position")
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,[x,y],self.origin)
            try:
                self.advangleboth(thetas[0], thetas[1])
            except:
                print("Cannot move to position")
        else:
            print("Indicated pump not recognized")

    def movetowell(self, effector, target_wellid):
        """Move indicated effector to target well."""
        
        if target_wellid == "purge":
            self.movetopurge(effector)
            return
        elif target_wellid not in self.wellids:
            print("The target well is not in the current plate layout")
            return
        
        if effector == "center":
            thetas = kf.angle_lookup(target_wellid,self.wellids,self.alltheta1,self.alltheta2)
            self.advangleboth(thetas[0], thetas[1])
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            wellthetas = kf.angle_lookup(target_wellid,self.wellids,self.alltheta1,self.alltheta2)
            center = kf.forward_kinematics(self.L1,self.L2,self.L3,wellthetas[0],wellthetas[1])
            #print (center)
            #print (pump_label)
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
        else:
            print("Indicated pump not recognized")
    
    # Simple move to theta function. Moves indicated effector to target well.
    
    def movetothetas(self, effector, targetthetas):
        """Move indicated effector to target well."""
        
        if effector == "center":
            self.advangleboth(targetthetas[0], targetthetas[1])
        elif effector in {"p1", "p2", "p3", "p4"}:
            pump_label = effector.replace("p","N")
            center = kf.forward_kinematics(self.L1,self.L2,self.L3,targetthetas[0],targetthetas[1])
            thetas = kf.inverse_kinematics_multi(self.L1,self.L2,self.L3,self.Ln,pump_label,center,self.origin)
            self.advangleboth(thetas[0], thetas[1])
        else:
            print("Indicated pump not recognized")
            
        
    # Home function, returns effector to set home position
    
    def return_home(self):
        """Return effector to set home position"""
        
        self.advangleboth(self.home[0], self.home[1])
        
    # Moves selected pump to purge location
    
    def movetopurge(self,pumpid):
        """Move selected pump to purge location"""
        
        self.movetothetas(pumpid,self.purge)

    # Allows the user to select a pump, and purge the lines by holding down the purge button.
    def manualpurge(self):
        """Allow the user to select a pump, and purge the lines by holding down the purge button."""
        
        while True:
            ool = 1
            pumpid = input("Which pump would you like to purge? \n Type 'p1', 'p2', 'p3', or 'p4' and hit enter.   ")
            
            if pumpid in {"p1", "p2", "p3", "p4"}:
                self.movetothetas(pumpid,self.purge)
                print("Press and hold the purge button to begin purging line. Release the button to stop.")
                timer = 0
                outerloop = 1
                while outerloop == 1:
                    outerloop = 1
                    if self.purgebutton.value() == 0:
                        timer = 0
                        self.dispense(pumpid,10)
                        #print(self.purgebutton.value())
                        time.sleep(.01)
                    if self.purgebutton.value() == 1:
                        time.sleep(.1)
                        timer=timer+1
                    if self.purgebutton.value() == 1 and timer >= 40:
                        stop = input("Type stop if you want stop. Type anything else if you'd like to continue purging this pump.  ")
                        if stop == "stop" or self.purgebutton.value() == 0:
                            timer = 0
                            outerloop = 0
                        else:
                            timer = 0
            cont = input("Would you like to home another pump? \n Type 'yes' or 'no'   ")
            if cont == "yes":
                ool = 1
            if cont != "yes":
                self.return_home()
                break
        
        
    
    ##%% DISPENSE FUNCTIONS
    
    # Dispenses the commanded amount of liquid from the indicated pump (10 microliter aliquots)
    def dispense(self, pumpLabel, desiredamount):
        """Dispense the commanded amount of liquid from the indicated pump (10 microliter aliquots)."""
        
        actualamount = round(desiredamount/10)*10
        cycles = round(actualamount/10)
        
        # escape if nothing gets pumped
        if cycles == 0:
            return

        print("dispensing", actualamount)

        pumpDictionary = {
            "p1": self.pump1,
            "p2": self.pump2,
            "p3": self.pump3,
            "p4": self.pump4
        }    
        
        if pumpLabel in pumpDictionary: 
            pump = pumpDictionary.get(pumpLabel)
            for i in range(cycles):
                pump.value(1)
                time.sleep(.1)
                #print("energize")
                pump.value(0)
                time.sleep(.1)
                #print("de-energize")
                #print(i)

        elif pumpLabel == "center":
            pass
        else:
            print("Indicated pump label ", pumpLabel, " is not recognized")

    # Finds the endpoints, run first whenever waking the machine!
    
    def initialize(self):
        """Find the endpoints of armature travel."""
        
        self.motor2_sleep.value(1)
        # Calibrates Motor 1, (Upper Motor)
        
        while self.lsfront.value() != 0:
            self.motor1_onestep(1)
            time.sleep(self.stepdelay*3)
        if self.lsfront.value() == 0:
            print("Front limit reached")
            self.current[0] = 0
        
        # Calibrates Motor 2, (Lower Motor)
        self.motor2_sleep.value(0)
        
        while self.lsrear.value() != 0:
            self.motor1_onestep(0)
            self.current[0] = self.current[0] + self.stepsize
            self.motor2_onestep(0)
            time.sleep(self.stepdelay*3)
        if self.lsrear.value() == 0:
                print("Rear limit reached")
                self.current[1] = 180
        
        self.return_home()
        
    # Hardware Check, checks if everything is working properly, used to validate wiring during build.
    
    def hardwarecheck(self):
        """Hardware Check, check if everything is working properly, use to validate wiring during build."""
    
        self.motor2_sleep.value(1)
        # Calibrates Motor 1, (Upper Motor)
        print("Testing top motor. Armature movement should be clockwise, moving to front of Sidekick")
        while self.lsfront.value() != 0:
            self.motor1_onestep(1)
            time.sleep(self.stepdelay*3)
        if self.lsfront.value() == 0:
            print("Front limit switch triggered")
            self.current[0] = 0
        
        # Calibrates Motor 2, (Lower Motor)
        self.motor2_sleep.value(0)
        
        print("Testing lower motor. Armature movement should be counterclockwise, moving to rear of Sidekick")
        while self.lsrear.value() != 0:
            self.motor1_onestep(0)
            self.current[0] = self.current[0] + self.stepsize
            self.motor2_onestep(0)
            time.sleep(self.stepdelay*3)
        if self.lsrear.value() == 0:
                print("Rear limit switch triggered")
                self.current[1] = 180
        
        self.return_home()
        
        print("testing pump 1 (closest to front). You should hear clicking as the pump energizes.")
        
        self.dispense("p1", 100)
        print("testing pump 2.")
        self.dispense("p2", 100)
        print("testing pump 3.")
        self.dispense("p3", 100)
        print("testing pump 4.")
        self.dispense("p4", 100)
        
        print("testing purge button. Click the purge button, then release it. \nThe Sidekick will output whether it detects that the button is held or released.")
        
        time.sleep(5)
        
        ot = 1
        btest = 1
        while ot == 1:
            if self.purgebutton.value() == 0:
                while btest == 1:
                    if self.purgebutton.value() == 0:
                        print("purge button pressed")
                        time.sleep(.1)
                    if self.purgebutton.value() == 1:
                        print("purge button released")
                        btest =0
                        ot = 0
                     

        print("Hardware check complete. If any components did not behave as described, please troubleshoot wiring")
        
    
    # Releases both motors
    
    def release(self):
        """Release both motors"""

        self.motor1_sleep.value(1)
        self.motor2_sleep.value(1)
    
    # Wakes both motors
    
    def wake(self):
        """Wake both motors"""
        
        self.motor1_sleep.value(0)
        self.motor2_sleep.value(0)
        self.initialize()

    
    def current_xy(self):
        """returns the current [x, y] position as a list"""
        return kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
    
    def print_angular_position(self):
        """prints the current [theta_1, theta_2] position as a list"""
        print(self.current[0],self.current[1])
        
    def print_current_xy(self):
        """returns the current [x, y] position as a list"""
        print(kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1]))


    # Allows the user to move the effector freely, then prints position.
    
    def freemove(self):
        """Allow the user to move the effector freely, then print position."""
        
        nearestwell = input("enter closest well  ")
        self.movetowell("center", nearestwell) 
        while True:
            direction = input("enter direction with w,a,s,d, the hit enter. If finished, enter 'finished'  ")
            if direction == "s":
                newangles = kf.down(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "w":
                newangles = kf.up(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "a":
                newangles = kf.left(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "d":
                newangles = kf.right(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "finished":
                position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                print("Freemove ended. Current angles are", self.current, "Current location is", position)
                break
            
    def purgeset(self):
        """Set the location of the purge vessel"""

        nearestwell = input("enter closest well to purge location  ")
        thetas =  kf.angle_lookup(nearestwell,self.wellids,self.alltheta1,self.alltheta2)
        self.advangleboth(thetas[0], thetas[1])
        while True:
            direction = input("enter direction with w,a,s,d, the hit enter.\n If centered over the purge location, enter 'finished'  ")
            if direction == "s":
                newangles = kf.down(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "w":
                newangles = kf.up(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "a":
                newangles = kf.left(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "d":
                newangles = kf.right(self.current[0],self.current[1])[0:2]
                self.advangleboth(newangles[0], newangles[1])
            if direction == "finished":
                position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                print("Freemove ended. Current angles are", self.current, "Current location is", position)
                break
        file = open("purge1.txt", "w")
        file.write(str(self.current[0]) + "\n")
        file.write(str(self.current[1]))
        file.close()
        self.return_home()

    # Regenerates the plate map. Use if plating for the first time, or if using new plates.
    def remap(self):
        """Regenerate the plate map. Use if plating for the first time, or if using new plates."""
        
        
        while True:
            calibrate = input("Calibrate? Type 'yes' to continue, or 'no' to stop  ")
            if calibrate == "no":
                break
            if calibrate == "yes":
                
                
                calcorners = ['a1','a12','h1','h12']
                calcorner_pos = []
                
                for x in range(4):
                    thetas =  kf.angle_lookup(calcorners[x],self.wellids,self.alltheta1,self.alltheta2)
                    if x == 0:
                        print("Center over the top left well")
                    if x == 1:
                        print("Center over the top right well")
                    if x == 2:
                        print("Center over the bottom left well")
                    if x == 3:
                        print("Center over the bottom right well")
                    
                    self.advangleboth(thetas[0], thetas[1])
                    
                    while True:
                        direction = input("enter direction with w,a,s,d, the hit enter. If finished, enter 'calibrate'  ")
                        if direction == "s":
                            newangles = kf.down(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "w":
                            newangles = kf.up(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "a":
                            newangles = kf.left(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "d":
                            newangles = kf.right(self.current[0],self.current[1])[0:2]
                            self.advangleboth(newangles[0], newangles[1])
                        if direction == "calibrate":
                            position = kf.forward_kinematics(self.L1,self.L2,self.L3,self.current[0],self.current[1])
                            print("Calibration complete! Corrected angles are", self.current, "Corrected location is", position)
                            calcorner_pos.append(position)
                            break
                results = plategen.remap_plate(calcorner_pos[0],calcorner_pos[1],calcorner_pos[2],calcorner_pos[3],self.L1,self.L2,self.L3,self.origin)
                print(results[0])
                print(results[1])
                print(results[2])
                file = open("platemap1.txt", "w")
                file.write("theta_one \n")
                for coord in results[0]:
                    file.write(str(coord) + "\n")
                file.write("theta_two \n")
                for coord in results[1]:
                    file.write(str(coord) + "\n")
                file.write("well_ids \n")
                for coord in results[2]:
                    file.write(coord + "\n")
                file.close()
                self.plateinfo = self.loadplate()
                self.alltheta1 = self.plateinfo[0]
                self.alltheta2 = self.plateinfo[1]
                self.wellids = self.plateinfo[2]
                self.return_home()
    
    # Reads a CSV file and turns it into commands.
    
    @staticmethod
    def read_instructions(filename):
        """Read a CSV file and turn it into commands."""
        
        test = open(filename)
        stuff = test.read()
        stuff = stuff.replace("\r", "").split("\n")
        stuff = stuff[1:]

        cmd = [stuff[i].split(",") for i in range(len(stuff) - 1)]

        #print(cmd)

        return cmd
    
    # Takes a CSV file of instructions, and plates them.
    
    def execute_protocol(self, filename="saved_protocol.csv"):
        """Take a CSV file of instructions, and plate them."""

        commands = self.read_instructions(filename)
        print(commands)
        for cmd in commands:
            pumpid, targetwell, desiredamount = cmd[0:3]
            #print(targetwell)
            #print(pumpid)
            #print(desiredamount)
            
            self.movetowell(pumpid,targetwell)
            self.dispense(pumpid, float(desiredamount))


                
#alpha = Sidekick(7,3,10,0.5,[0,0],[90,178],[119.484,171.701]) # This is the template of the default Sidekick.


```

### kinematicsfunctions.py

```python
## Import libraries

import math

#%% All measurements are in cm and degrees
#%% Lookup table, converts wells formatted as 'a1' ... 'h12' to joint angles

def angle_lookup(well,wellids,alltheta1,alltheta2):
    #wellids = ['a12','a11','a10','a9','a8','a7','a6','a5','a4','a3','a2','a1','b12','b11','b10','b9','b8','b7','b6','b5','b4','b3','b2','b1','c12','c11','c10','c9','c8','c7','c6','c5','c4','c3','c2','c1','d12','d11','d10','d9','d8','d7','d6','d5','d4','d3','d2','d1','e12','e11','e10','e9','e8','e7','e6','e5','e4','e3','e2','e1','f12','f11','f10','f9','f8','f7','f6','f5','f4','f3','f2','f1','g12','g11','g10','g9','g8','g7','g6','g5','g4','g3','g2','g1','h12','h11','h10','h9','h8','h7','h6','h5','h4','h3','h2','h1']
    #alltheta1 = [119.4841,117.6138,114.5787,110.2216,104.4481,97.28982,88.94462,79.75737,70.13718,60.45672,50.9865,41.88039,110.6423,108.5257,105.3983,101.1829,95.85575,89.47376,82.18741,74.2247,65.84932,57.31055,48.80589,40.46561,102.4427,100.2429,97.16377,93.17305,88.27757,82.53652,76.06442,69.02013,61.58364,53.92882,46.20107,38.50505,94.71713,92.53403,89.57684,85.83804,81.33793,76.13086,70.30529,63.97631,57.27198,50.31734,43.22037,36.06285,87.31276,85.21027,82.41408,78.93111,74.7873,70.03075,64.73105,58.97418,52.85399,46.46227,39.87944,33.16767,80.08457,78.10734,75.49476,72.26294,68.44019,64.06895,59.20506,53.91427,48.26676,42.3305,36.16477,29.81468,72.88291,71.06822,68.65616,65.66992,62.13932,58.10236,53.60484,48.69798,43.43468,37.86483,32.03041,25.96063,65.53224,63.92112,61.72933,58.98761,55.72801,51.98577,47.79946,43.20942,38.25514,32.97155,27.3848,21.50715]
    #alltheta2 = [171.7007,165.8025,159.4164,152.4932,145.05,137.2078,129.2057,121.3677,114.0266,107.4482,101.7913,97.11273,169.0437,163.2183,157.0534,150.547,143.7473,136.7667,129.7804,123.0038,116.6541,110.9124,105.9007,101.6799,167.3756,161.709,155.8243,149.7399,143.5099,137.229,131.0273,125.0557,119.4647,114.3838,109.9079,106.0939,166.5481,161.0759,155.4819,149.7911,144.0545,138.349,132.7729,127.4364,122.4487,117.9062,113.8844,110.4347,166.4537,161.1825,155.8659,150.5293,145.2169,139.9906,134.926,130.1059,125.6129,121.5214,117.8931,114.7745,167.0239,161.9423,156.8782,151.8537,146.9053,142.0826,137.4445,133.0553,128.979,125.2755,121.9969,119.1865,168.2294,163.3136,158.47,153.7154,149.0787,144.599,140.3229,136.3011,132.5854,129.2257,126.268,123.7544,170.088,165.3015,160.6399,156.1127,151.7408,147.5543,143.59,139.8893,136.4952,133.4516,130.8018,128.5897,]
    
    
    index = wellids.index(well)
    theta1 = alltheta1[index]
    theta2 = alltheta2[index]
        
    return [theta1,theta2]

#%% Find the standard position angle from the positive x axis given a point

def find_standard_position_angle(point):

    x, y = point[0:2]

    if x == 0:
        ref_angle = 90
    else:
        ref_angle = math.degrees(math.atan(y/x))
    
    # Finds the quadrant
    
    if x >= 0 and y >= 0:
        quadrant = 1
    elif x <= 0 <= y:
        quadrant = 2
    elif x <= 0 and y <= 0:
        quadrant = 3
    else:
        quadrant = 4
    
    # Finds the standard angle given reference angle and quadrant
    
    if quadrant in {1, 4}:
        standard_angle = 0 + ref_angle
    elif quadrant in {2, 3}:
        standard_angle = 180 + ref_angle
    else:
        raise ValueError("quadrant not in [1,2,3,4]!")
        
    if standard_angle < 0:
        standard_angle = standard_angle + 360
        
    return standard_angle

#%% Calculating intersection of two circles (http://paulbourke.net/geometry/circlesphere/), (https://stackoverflow.com/questions/55816902/finding-the-intersection-of-two-circles)

def get_intersections(x0, y0, r0, x1, y1, r1):
    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1

    d=math.sqrt((x1-x0)**2 + (y1-y0)**2)
    
    # non intersecting
    if d > r0 + r1 :
        return None
    # One circle within other
    if d < abs(r0-r1):
        return None
    # coincident circles
    if d == 0 and r0 == r1:
        return None
    else:
        a=(r0**2-r1**2+d**2)/(2*d)
        h=math.sqrt(r0**2-a**2)
        x2=x0+a*(x1-x0)/d   
        y2=y0+a*(y1-y0)/d   
        x3=round(x2+h*(y1-y0)/d,4)     
        y3=round(y2-h*(x1-x0)/d,4) 

        x4=round(x2-h*(y1-y0)/d,4)
        y4=round(y2+h*(x1-x0)/d,4)
        
        return (x3, y3, x4, y4)

#%% Inverse Kinematics calculations


def inverse_kinematics(L1,L2,L3,origin,p4):
    
    p1 = get_intersections(p4[0],p4[1],L3,origin[0],origin[1],L1) # Get the possible locations of point 1

    if p1 is None:
        print("No possible orientations")
    else:
        p1a = [p1[0],p1[1]] # Conformation 1
        p1b = [p1[2],p1[3]] # Conformation 2
        
        ## EVALUATES CONFORMATION 1
        
        con1p3vector = [p4[0] - p1a[0],p4[1]-p1a[1]] # Finds the vector extending from p1 to p4
        con1p3standangle = find_standard_position_angle(con1p3vector) # Finds the position angle for that vector
        
        #Calculates p2 and p3 by adding the length of L2 in the opposite direction of the postion angle drawn between p1 and p4
        
        con1p3 = [round(p1a[0] + L2 * math.cos(math.radians(con1p3standangle+180)),4),round(p1a[1] + L2 * math.sin(math.radians(con1p3standangle+180)),4)]
        con1p2 = [round(origin[0] + L2 * math.cos(math.radians(con1p3standangle+180)),4),round(origin[1] + L2 * math.sin(math.radians(con1p3standangle+180)),4)]
        
        #Finds the position angles for conformation 1
        
        con1theta1 = find_standard_position_angle(p1a)
        con1theta2 = find_standard_position_angle(con1p2)
        
        ## EVALUATES CONFORMATION 2, (Same calculation as conformation 1 but with p1b)
        
        con2p3vector = [p4[0] - p1b[0],p4[1]-p1b[1]] # Finds the vector extending from p1 to p4
        con2p3standangle = find_standard_position_angle(con2p3vector) # Finds the position angle for that vector
        
        #Calculates p2 and p3 by adding the length of L2 in the opposite direction of the postion angle drawn between p1 and p4
        
        con2p3 = [round(p1b[0] + L2 * math.cos(math.radians(con2p3standangle+180)),4),round(p1b[1] + L2 * math.sin(math.radians(con2p3standangle+180)),4)]
        con2p2 = [round(origin[0] + L2 * math.cos(math.radians(con2p3standangle+180)),4),round(origin[1] + L2 * math.sin(math.radians(con2p3standangle+180)),4)]
        
        #Finds the position angles for conformation 1
        
        con2theta1 = find_standard_position_angle(p1b)
        con2theta2 = find_standard_position_angle(con2p2)
        
        ## Choosing Between Conformation 1 and 2
        
        theta1check = [con1theta1,con2theta1]
        theta2check = [con1theta2,con2theta2]
        
        #Creates arrays of possible thetas to evaluate
        theta1possible = []
        theta2possible = []
        
        #Checks the mechanical constraints of the possible angles
        for i in range(len(theta1check)):
            if theta1check[i] <= 195:
                theta1possible.append(i)
        
        for i in range(len(theta2check)):
            if theta2check[i] <= 195:
                theta2possible.append(i)
        
        intersect = set.intersection(set(theta1possible),set(theta2possible))
        
        if not intersect: # empty set
            print("All possible orientations violate mechanical constraints")
            return 
 
        elif len(intersect) > 1:
            #print("Two possible orientations, first orientation selected")
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
        elif list(intersect)[0] == 0: #conformation 1 chosen
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
        elif list(intersect)[0] == 1: #conformation 2 chosen
            theta1 = con2theta1
            theta2 = con2theta2
            p1 = p1b
            p2 = con2p2
            p3 = con2p3
        else:
            raise RuntimeError("no conformation was chosen")
            
        return[theta1,theta2,p1,p2,p3]

#%% MultiChannel Inverse Kinematics

def inverse_kinematics_multi(L1,L2,L3,Ln,N,ptarget,origin):

    # First we need to define the length from P3 to the target nozzle N, we can do this with some trig
    
    if N in { "N1", "N3"}:
        # Formula for this length for nozzles 1 and 3
        nlength = math.sqrt(math.pow((L3-(Ln/math.sqrt(2))),2) + math.pow((Ln/math.sqrt(2)),2))
    elif N in {"N2", "N4"}:
        #Formula for this length for nozzles 2 and 4
        nlength = math.sqrt(math.pow((L3+(Ln/math.sqrt(2))),2) + math.pow((Ln/math.sqrt(2)),2))
    else:
        raise ValueError("input N is not allowed")
        
    p1 = get_intersections(ptarget[0],ptarget[1],nlength,origin[0],origin[1],L1) # Get the possible locations of point 1
    
    if p1 is None:
        print("No possible orientations")
    else:
        p1a = p1[0:2] # Conformation 1
        p1b = p1[2:4] # Conformation 2
        
        ## Solves for N, Conformation 1

        n1vector = [ptarget[0]-p1a[0],ptarget[1]-p1a[1]] #finds the n1 vector
        n1standtheta = find_standard_position_angle(n1vector) #Finding the standard position angle for the n1 vector
        
        ## Changes the calculation based on which nozzle we're calculating for
        if N == "N1":
            # For N1 and N3, the triangle drawn faces towards the origin, so the adjacent leg is L3 - Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N1 Nozzle is above center position, so to find the center position we go down
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N3":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We add the offset to the standard angle, because the N3 Nozzle is below the center position, so to find the center position we go up
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        elif N == "N2":
            # For N2 and N4, we change the offset calculation. The triangle drawn faces away from the origin, so the adjacent leg is L3 + Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N2 Nozzle is above center position, so to find the center position we go down
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N4":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We add the offset from the standard angle, because the N4 Nozzle is below center position, so to find the center position we go up
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        else:
            raise ValueError("input N is not allowed")

        ## After using the offset, standard angle, and length of L3 to find P4, we can use our original Inverse Kinematics function
        results = inverse_kinematics(L1,L2,L3,origin,p4)
        con1theta1 = results[0]
        con1theta2 = results[1]
        con1p1 = results[2]
        con1p2 = results[3]
        con1p3 =results[4]
        
        ## Solves for N Conformation 2
    
        n1vector = [ptarget[0]-p1b[0],ptarget[1]-p1b[1]] #finds the n1 vector
        n1standtheta = find_standard_position_angle(n1vector) #Finding the standard position angle for the n1 vector
        
        ## Changes the calculation based on which nozzle we're calculating for
        if N == "N1":
            # For N1 and N3, the triangle drawn faces towards the origin, so the adjacent leg is L3 - Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N1 Nozzle is above center position, so to find the center position we go down
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N3":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We add the offset to the standard angle, because the N3 Nozzle is below the center position, so to find the center position we go up
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        elif N == "N2":
            # For N2 and N4, we change the offset calculation. The triangle drawn faces away from the origin, so the adjacent leg is L3 + Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N2 Nozzle is above center position, so to find the center position we go down
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N4":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We add the offset from the standard angle, because the N4 Nozzle is below center position, so to find the center position we go up
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        else:
            raise ValueError("input N is not allowed")

        results = inverse_kinematics(L1,L2,L3,origin,p4con2)
        con2theta1 = results[0]
        con2theta2 = results[1]
        con2p1 = results[2]
        con2p2 = results[3]
        con2p3 =results[4]
        
        ## Choosing Between Conformation 1 and 2
            
        theta1check = [con1theta1,con2theta1]
        theta2check = [con1theta2,con2theta2]
        
        #Creates arrays of possible thetas to evaluate by checking mechanical constraints of the possible angles
        theta1possible = [i for i,v in enumerate(theta1check) if v <= 195]
        theta2possible = [i for i,v in enumerate(theta2check) if v <= 195]        
        intersect = set.intersection(set(theta1possible),set(theta2possible))
        
        if not intersect: # empty
            print("All possible orientations violate mechanical constraints")
        
        elif len(intersect) > 1:
            #print("Two possible orientations, first orientation selected")
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
            p4 = p4
        elif list(intersect)[0] == 0: #conformation 1 chosen
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
            p4 = p4
        elif list(intersect)[0] == 1: #conformation 2 chosen
            theta1 = con2theta1
            theta2 = con2theta2
            p1 = p1b
            p2 = con2p2
            p3 = con2p3
            p4 =p4con2
        else:
            raise RuntimeError("no conformation was chosen")
            
        finalresults = [theta1,theta2,p1,p2,p3,p4]
        return finalresults

#%% ForwardKinematics

def forward_kinematics(L1,L2,L3,theta1,theta2):
    #Define each of the vertex points by the angle and leg length
    p1 = [L1*math.cos(math.radians(theta1)),L1*math.sin(math.radians(theta1))]
    p2 = [L2*math.cos(math.radians(theta2)),L2*math.sin(math.radians(theta2))]
    p3 = [p1[0]+p2[0], p1[1]+p2[1]]

    #Parallel to L2, so add L3 and L2 to get the total length of the leg, multiply by theta 2, and subtract from p3
    p4 = [p3[0]-(L2+L3)*math.cos(math.radians(theta2)),p3[1]-(L2+L3)*math.sin(math.radians(theta2))]
    
    return p4

#%% Simple movement in the xy plane .5 mm intervals. Up is in reference to the plate and the center of the dispenser.

def motion(setting, theta1, theta2):
    p4 = forward_kinematics(setting['L1'], setting['L2'], setting['L3'], theta1, theta2)
    p4[0] += setting['offset_p4_0']
    p4[1] += setting['offset_p4_1']
    result = inverse_kinematics(setting['L1'], setting['L2'], setting['L3'],setting['origin'],p4) + p4 
    return result

def up(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":-0.05, "offset_p4_1":0.00}
    return motion(setting, theta1, theta2)

def down(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":0.05, "offset_p4_1":0.00}
    return motion(setting, theta1, theta2)

def left(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":0.00, "offset_p4_1":-0.05}
    return motion(setting, theta1, theta2)

def right(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":0.00, "offset_p4_1":0.05}
    return motion(setting, theta1, theta2)
    
    
```

### main.py

```python
from Sidekick_object import Sidekick
from parser import com_parser, gcode_parser


# Defines an instance of the Sidekick
alpha = Sidekick(7,3,10,0.5,[0,0],[90,178],[119.484,171.701])

# On startup, homes position
alpha.initialize()


# Dictionary of available commands
comdict = {
        "initialize" : alpha.initialize,
        "hardware check" : alpha.hardwarecheck,
        "xy position" : alpha.print_current_xy,
        "angular position" : alpha.print_angular_position,
        "free move" : alpha.freemove,
        "sleep" : alpha.release,
        "wake" : alpha.wake,
        "return home" : alpha.return_home,
        "manual purge" : alpha.manualpurge,
        "remap" : alpha.remap,
        "set purge" : alpha.purgeset,
        "execute saved protocol" : alpha.execute_protocol,
        "g28" : alpha.return_home,  # G-CODE equivalent comamnds
        "g29" : alpha.remap,
        "m17" : alpha.wake,
        "m18" : alpha.release,
        "m24" : alpha.execute_protocol
        }

# Main loop, awaiting command

while True:
    # Get User Input
    command = input("awaiting command\n")
    command = command.lower()
    
    if command in comdict:  # handle simple commands without arguments
        comdict[command]()
    elif command == "":     # handle blank line
        continue
    else:
        if command[0]=="p":   # interpret it as our own simplified command type
            pumpid, wellid, volume = com_parser(command)
            alpha.movetowell(pumpid,wellid)
            alpha.dispense(pumpid,volume)
        elif command[0]=="g":  # interpret it as gcode
            x, y, volumes = gcode_parser(command)
            
            #print([x,y])
            # if x or y (or both) are not specified by G-Code, then use the current value
            currentXY = alpha.current_xy()
           
            if x is None:  
                x = currentXY[0]
            if y is None:
                y = currentXY[1]

            # move to desired position
            alpha.movetoXY("center", x, y)

            # perform dispense for each pump in order 
            # NOTE: This is probably not the desired operation, as it will dispense from these pumps with the 
            #       center defined as above, rather than with the given pump output in that location.
            
            if volumes is not None:
                for (i,v) in enumerate(volumes):
                    pumpid = "p"+str(i+1)
                    alpha.dispense(pumpid, v)
        

            
```

### parser.py

```python

def gcode_parser(command):
    """Parse Gcode commands"""
    x = None
    y = None
    volumes = None

    tokens = command.split()
    tokens.reverse()

    #print(tokens)
    cmd = tokens.pop()

    if cmd != "g0":
        print("error:  gcode command ", cmd, "is not supported.  Only G0 based moves are supported.")
        return [x, y, volumes]
    
    while (tokens):
        cmd = tokens.pop()

        if cmd == "x": # handle space between X and input
            x = float(tokens.pop())/10.
        elif cmd[0] == "x": #handle no space after x
            x = float(cmd[1:])/10.  # gcode uses units of millimeters, convert to centimeters
        elif cmd == "y":
            y = float(tokens.pop())/10.
        elif cmd[0] == "y":
            y = float(cmd[1:])/10.
        elif cmd == "e":
            volumes = [float(v) for v in tokens.pop().split(";")] # assume uL units
        elif cmd[0] == "e":
            volumes = [float(v) for v in cmd[1:].split(";")]

    return [x, y, volumes]


def com_parser (command):
    """Parse the movement or dispense command string."""
    
    tokens = command.split()

    # Indicated Pump
    pumpid = tokens[0]
    
    # Target Well
    try:
        wellid = tokens[1]
    except:
        wellid = []
    
    # Target Volume
    if len(tokens) == 3:
        try:
            volume = float(tokens[2])
        except:
            print("Volume (microliters) not recognized, please enter in a numerical value")
            volume = 0
    else:
        volume = 0
    
    return [pumpid,wellid,volume]

```

### plategen.py

```python
import kinematicsfunctions as kf

# This function interpolates the remaining well locations from the four corner wells. Used when setting up a new plate, or if the Sidekick is plating inaccurately.
def remap_plate(A1,A12,H1,H12,L1,L2,L3,origin):
    """Given the four corner wells and the Sidekick dimensions, interpolate the other well locations"""
    def linear_interpolate(startwell,endwell,wells):
        """Interpolates the coordinates between a given start well, and end well."""
        
        dist_between_wells_x = (endwell[0] - startwell[0])/ (wells-1)
        dist_between_wells_y = (endwell[1] - startwell[1]) / (wells-1)

        final_coordinates = [[startwell[0] + i * dist_between_wells_x, startwell[1] + i * dist_between_wells_y] for i in range(wells)]
        return final_coordinates


    # Calculates the outer edges
    first_col = linear_interpolate(A1, H1, 8)
    last_col = linear_interpolate(A12, H12,8)
    all_coord = [linear_interpolate(first_col[i], last_col[i], 12) for i in range(len(first_col))]

    # Flattens list
    flattened_coords = [val for sublist in all_coord for val in sublist]

    # Uses inverse kinematics to convert to thetas
    thetas = [kf.inverse_kinematics(L1,L2,L3,origin,flattened_coords[i]) for i in range(len(flattened_coords))]
    theta1 = [thetas[i][0] for i in range(len(thetas))]
    theta2 = [thetas[i][1] for i in range(len(thetas))]

    # Fills well ID list
    row = ["a","b","c","d","e","f","g","h"]
    column = list(map(str, list(range(1,13))))
    wellids = [row[i] + column[j] for i in range(len(row)) for j in range(len(column))]
    
    return [theta1,theta2,wellids]

```


```

### kinematicsfunctions.py

```python
## Import libraries

import math

#%% All measurements are in cm and degrees
#%% Lookup table, converts wells formatted as 'a1' ... 'h12' to joint angles

def angle_lookup(well,wellids,alltheta1,alltheta2):
    #wellids = ['a12','a11','a10','a9','a8','a7','a6','a5','a4','a3','a2','a1','b12','b11','b10','b9','b8','b7','b6','b5','b4','b3','b2','b1','c12','c11','c10','c9','c8','c7','c6','c5','c4','c3','c2','c1','d12','d11','d10','d9','d8','d7','d6','d5','d4','d3','d2','d1','e12','e11','e10','e9','e8','e7','e6','e5','e4','e3','e2','e1','f12','f11','f10','f9','f8','f7','f6','f5','f4','f3','f2','f1','g12','g11','g10','g9','g8','g7','g6','g5','g4','g3','g2','g1','h12','h11','h10','h9','h8','h7','h6','h5','h4','h3','h2','h1']
    #alltheta1 = [119.4841,117.6138,114.5787,110.2216,104.4481,97.28982,88.94462,79.75737,70.13718,60.45672,50.9865,41.88039,110.6423,108.5257,105.3983,101.1829,95.85575,89.47376,82.18741,74.2247,65.84932,57.31055,48.80589,40.46561,102.4427,100.2429,97.16377,93.17305,88.27757,82.53652,76.06442,69.02013,61.58364,53.92882,46.20107,38.50505,94.71713,92.53403,89.57684,85.83804,81.33793,76.13086,70.30529,63.97631,57.27198,50.31734,43.22037,36.06285,87.31276,85.21027,82.41408,78.93111,74.7873,70.03075,64.73105,58.97418,52.85399,46.46227,39.87944,33.16767,80.08457,78.10734,75.49476,72.26294,68.44019,64.06895,59.20506,53.91427,48.26676,42.3305,36.16477,29.81468,72.88291,71.06822,68.65616,65.66992,62.13932,58.10236,53.60484,48.69798,43.43468,37.86483,32.03041,25.96063,65.53224,63.92112,61.72933,58.98761,55.72801,51.98577,47.79946,43.20942,38.25514,32.97155,27.3848,21.50715]
    #alltheta2 = [171.7007,165.8025,159.4164,152.4932,145.05,137.2078,129.2057,121.3677,114.0266,107.4482,101.7913,97.11273,169.0437,163.2183,157.0534,150.547,143.7473,136.7667,129.7804,123.0038,116.6541,110.9124,105.9007,101.6799,167.3756,161.709,155.8243,149.7399,143.5099,137.229,131.0273,125.0557,119.4647,114.3838,109.9079,106.0939,166.5481,161.0759,155.4819,149.7911,144.0545,138.349,132.7729,127.4364,122.4487,117.9062,113.8844,110.4347,166.4537,161.1825,155.8659,150.5293,145.2169,139.9906,134.926,130.1059,125.6129,121.5214,117.8931,114.7745,167.0239,161.9423,156.8782,151.8537,146.9053,142.0826,137.4445,133.0553,128.979,125.2755,121.9969,119.1865,168.2294,163.3136,158.47,153.7154,149.0787,144.599,140.3229,136.3011,132.5854,129.2257,126.268,123.7544,170.088,165.3015,160.6399,156.1127,151.7408,147.5543,143.59,139.8893,136.4952,133.4516,130.8018,128.5897,]
    
    
    index = wellids.index(well)
    theta1 = alltheta1[index]
    theta2 = alltheta2[index]
        
    return [theta1,theta2]

#%% Find the standard position angle from the positive x axis given a point

def find_standard_position_angle(point):

    x, y = point[0:2]

    if x == 0:
        ref_angle = 90
    else:
        ref_angle = math.degrees(math.atan(y/x))
    
    # Finds the quadrant
    
    if x >= 0 and y >= 0:
        quadrant = 1
    elif x <= 0 <= y:
        quadrant = 2
    elif x <= 0 and y <= 0:
        quadrant = 3
    else:
        quadrant = 4
    
    # Finds the standard angle given reference angle and quadrant
    
    if quadrant in {1, 4}:
        standard_angle = 0 + ref_angle
    elif quadrant in {2, 3}:
        standard_angle = 180 + ref_angle
    else:
        raise ValueError("quadrant not in [1,2,3,4]!")
        
    if standard_angle < 0:
        standard_angle = standard_angle + 360
        
    return standard_angle

#%% Calculating intersection of two circles (http://paulbourke.net/geometry/circlesphere/), (https://stackoverflow.com/questions/55816902/finding-the-intersection-of-two-circles)

def get_intersections(x0, y0, r0, x1, y1, r1):
    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1

    d=math.sqrt((x1-x0)**2 + (y1-y0)**2)
    
    # non intersecting
    if d > r0 + r1 :
        return None
    # One circle within other
    if d < abs(r0-r1):
        return None
    # coincident circles
    if d == 0 and r0 == r1:
        return None
    else:
        a=(r0**2-r1**2+d**2)/(2*d)
        h=math.sqrt(r0**2-a**2)
        x2=x0+a*(x1-x0)/d   
        y2=y0+a*(y1-y0)/d   
        x3=round(x2+h*(y1-y0)/d,4)     
        y3=round(y2-h*(x1-x0)/d,4) 

        x4=round(x2-h*(y1-y0)/d,4)
        y4=round(y2+h*(x1-x0)/d,4)
        
        return (x3, y3, x4, y4)

#%% Inverse Kinematics calculations


def inverse_kinematics(L1,L2,L3,origin,p4):
    
    p1 = get_intersections(p4[0],p4[1],L3,origin[0],origin[1],L1) # Get the possible locations of point 1

    if p1 is None:
        print("No possible orientations")
    else:
        p1a = [p1[0],p1[1]] # Conformation 1
        p1b = [p1[2],p1[3]] # Conformation 2
        
        ## EVALUATES CONFORMATION 1
        
        con1p3vector = [p4[0] - p1a[0],p4[1]-p1a[1]] # Finds the vector extending from p1 to p4
        con1p3standangle = find_standard_position_angle(con1p3vector) # Finds the position angle for that vector
        
        #Calculates p2 and p3 by adding the length of L2 in the opposite direction of the postion angle drawn between p1 and p4
        
        con1p3 = [round(p1a[0] + L2 * math.cos(math.radians(con1p3standangle+180)),4),round(p1a[1] + L2 * math.sin(math.radians(con1p3standangle+180)),4)]
        con1p2 = [round(origin[0] + L2 * math.cos(math.radians(con1p3standangle+180)),4),round(origin[1] + L2 * math.sin(math.radians(con1p3standangle+180)),4)]
        
        #Finds the position angles for conformation 1
        
        con1theta1 = find_standard_position_angle(p1a)
        con1theta2 = find_standard_position_angle(con1p2)
        
        ## EVALUATES CONFORMATION 2, (Same calculation as conformation 1 but with p1b)
        
        con2p3vector = [p4[0] - p1b[0],p4[1]-p1b[1]] # Finds the vector extending from p1 to p4
        con2p3standangle = find_standard_position_angle(con2p3vector) # Finds the position angle for that vector
        
        #Calculates p2 and p3 by adding the length of L2 in the opposite direction of the postion angle drawn between p1 and p4
        
        con2p3 = [round(p1b[0] + L2 * math.cos(math.radians(con2p3standangle+180)),4),round(p1b[1] + L2 * math.sin(math.radians(con2p3standangle+180)),4)]
        con2p2 = [round(origin[0] + L2 * math.cos(math.radians(con2p3standangle+180)),4),round(origin[1] + L2 * math.sin(math.radians(con2p3standangle+180)),4)]
        
        #Finds the position angles for conformation 1
        
        con2theta1 = find_standard_position_angle(p1b)
        con2theta2 = find_standard_position_angle(con2p2)
        
        ## Choosing Between Conformation 1 and 2
        
        theta1check = [con1theta1,con2theta1]
        theta2check = [con1theta2,con2theta2]
        
        #Creates arrays of possible thetas to evaluate
        theta1possible = []
        theta2possible = []
        
        #Checks the mechanical constraints of the possible angles
        for i in range(len(theta1check)):
            if theta1check[i] <= 195:
                theta1possible.append(i)
        
        for i in range(len(theta2check)):
            if theta2check[i] <= 195:
                theta2possible.append(i)
        
        intersect = set.intersection(set(theta1possible),set(theta2possible))
        
        if not intersect: # empty set
            print("All possible orientations violate mechanical constraints")
            return 
 
        elif len(intersect) > 1:
            #print("Two possible orientations, first orientation selected")
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
        elif list(intersect)[0] == 0: #conformation 1 chosen
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
        elif list(intersect)[0] == 1: #conformation 2 chosen
            theta1 = con2theta1
            theta2 = con2theta2
            p1 = p1b
            p2 = con2p2
            p3 = con2p3
        else:
            raise RuntimeError("no conformation was chosen")
            
        return[theta1,theta2,p1,p2,p3]

#%% MultiChannel Inverse Kinematics

def inverse_kinematics_multi(L1,L2,L3,Ln,N,ptarget,origin):

    # First we need to define the length from P3 to the target nozzle N, we can do this with some trig
    
    if N in { "N1", "N3"}:
        # Formula for this length for nozzles 1 and 3
        nlength = math.sqrt(math.pow((L3-(Ln/math.sqrt(2))),2) + math.pow((Ln/math.sqrt(2)),2))
    elif N in {"N2", "N4"}:
        #Formula for this length for nozzles 2 and 4
        nlength = math.sqrt(math.pow((L3+(Ln/math.sqrt(2))),2) + math.pow((Ln/math.sqrt(2)),2))
    else:
        raise ValueError("input N is not allowed")
        
    p1 = get_intersections(ptarget[0],ptarget[1],nlength,origin[0],origin[1],L1) # Get the possible locations of point 1
    
    if p1 is None:
        print("No possible orientations")
    else:
        p1a = p1[0:2] # Conformation 1
        p1b = p1[2:4] # Conformation 2
        
        ## Solves for N, Conformation 1

        n1vector = [ptarget[0]-p1a[0],ptarget[1]-p1a[1]] #finds the n1 vector
        n1standtheta = find_standard_position_angle(n1vector) #Finding the standard position angle for the n1 vector
        
        ## Changes the calculation based on which nozzle we're calculating for
        if N == "N1":
            # For N1 and N3, the triangle drawn faces towards the origin, so the adjacent leg is L3 - Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N1 Nozzle is above center position, so to find the center position we go down
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N3":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We add the offset to the standard angle, because the N3 Nozzle is below the center position, so to find the center position we go up
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        elif N == "N2":
            # For N2 and N4, we change the offset calculation. The triangle drawn faces away from the origin, so the adjacent leg is L3 + Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N2 Nozzle is above center position, so to find the center position we go down
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N4":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We add the offset from the standard angle, because the N4 Nozzle is below center position, so to find the center position we go up
            p4 = [round(p1a[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1a[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        else:
            raise ValueError("input N is not allowed")

        ## After using the offset, standard angle, and length of L3 to find P4, we can use our original Inverse Kinematics function
        results = inverse_kinematics(L1,L2,L3,origin,p4)
        con1theta1 = results[0]
        con1theta2 = results[1]
        con1p1 = results[2]
        con1p2 = results[3]
        con1p3 =results[4]
        
        ## Solves for N Conformation 2
    
        n1vector = [ptarget[0]-p1b[0],ptarget[1]-p1b[1]] #finds the n1 vector
        n1standtheta = find_standard_position_angle(n1vector) #Finding the standard position angle for the n1 vector
        
        ## Changes the calculation based on which nozzle we're calculating for
        if N == "N1":
            # For N1 and N3, the triangle drawn faces towards the origin, so the adjacent leg is L3 - Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N1 Nozzle is above center position, so to find the center position we go down
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N3":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3-(Ln/math.sqrt(2)))))
            # We add the offset to the standard angle, because the N3 Nozzle is below the center position, so to find the center position we go up
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        elif N == "N2":
            # For N2 and N4, we change the offset calculation. The triangle drawn faces away from the origin, so the adjacent leg is L3 + Ln/sqrt(2)
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We subtract the offset from the standard angle, because the N2 Nozzle is above center position, so to find the center position we go down
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta-n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta-n1thetaoffset)),4)]
        elif N == "N4":
            n1thetaoffset = math.degrees(math.atan((Ln/math.sqrt(2))/(L3+(Ln/math.sqrt(2)))))
            # We add the offset from the standard angle, because the N4 Nozzle is below center position, so to find the center position we go up
            p4con2 = [round(p1b[0]+L3*math.cos(math.radians(n1standtheta+n1thetaoffset)),4), round(p1b[1]+L3*math.sin(math.radians(n1standtheta+n1thetaoffset)),4)]
        else:
            raise ValueError("input N is not allowed")

        results = inverse_kinematics(L1,L2,L3,origin,p4con2)
        con2theta1 = results[0]
        con2theta2 = results[1]
        con2p1 = results[2]
        con2p2 = results[3]
        con2p3 =results[4]
        
        ## Choosing Between Conformation 1 and 2
            
        theta1check = [con1theta1,con2theta1]
        theta2check = [con1theta2,con2theta2]
        
        #Creates arrays of possible thetas to evaluate by checking mechanical constraints of the possible angles
        theta1possible = [i for i,v in enumerate(theta1check) if v <= 195]
        theta2possible = [i for i,v in enumerate(theta2check) if v <= 195]        
        intersect = set.intersection(set(theta1possible),set(theta2possible))
        
        if not intersect: # empty
            print("All possible orientations violate mechanical constraints")
        
        elif len(intersect) > 1:
            #print("Two possible orientations, first orientation selected")
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
            p4 = p4
        elif list(intersect)[0] == 0: #conformation 1 chosen
            theta1 = con1theta1
            theta2 = con1theta2
            p1 = p1a
            p2 = con1p2
            p3 = con1p3
            p4 = p4
        elif list(intersect)[0] == 1: #conformation 2 chosen
            theta1 = con2theta1
            theta2 = con2theta2
            p1 = p1b
            p2 = con2p2
            p3 = con2p3
            p4 =p4con2
        else:
            raise RuntimeError("no conformation was chosen")
            
        finalresults = [theta1,theta2,p1,p2,p3,p4]
        return finalresults

#%% ForwardKinematics

def forward_kinematics(L1,L2,L3,theta1,theta2):
    #Define each of the vertex points by the angle and leg length
    p1 = [L1*math.cos(math.radians(theta1)),L1*math.sin(math.radians(theta1))]
    p2 = [L2*math.cos(math.radians(theta2)),L2*math.sin(math.radians(theta2))]
    p3 = [p1[0]+p2[0], p1[1]+p2[1]]

    #Parallel to L2, so add L3 and L2 to get the total length of the leg, multiply by theta 2, and subtract from p3
    p4 = [p3[0]-(L2+L3)*math.cos(math.radians(theta2)),p3[1]-(L2+L3)*math.sin(math.radians(theta2))]
    
    return p4

#%% Simple movement in the xy plane .5 mm intervals. Up is in reference to the plate and the center of the dispenser.

def motion(setting, theta1, theta2):
    p4 = forward_kinematics(setting['L1'], setting['L2'], setting['L3'], theta1, theta2)
    p4[0] += setting['offset_p4_0']
    p4[1] += setting['offset_p4_1']
    result = inverse_kinematics(setting['L1'], setting['L2'], setting['L3'],setting['origin'],p4) + p4 
    return result

def up(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":-0.05, "offset_p4_1":0.00}
    return motion(setting, theta1, theta2)

def down(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":0.05, "offset_p4_1":0.00}
    return motion(setting, theta1, theta2)

def left(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":0.00, "offset_p4_1":-0.05}
    return motion(setting, theta1, theta2)

def right(theta1,theta2):
    #standard dimensions, change if needed.
    setting = {"L1":7, "L2":3, "L3":10, "origin":[0,0], "offset_p4_0":0.00, "offset_p4_1":0.05}
    return motion(setting, theta1, theta2)
    
    
```

### main.py

```python
from Sidekick_object import Sidekick
from parser import com_parser, gcode_parser


# Defines an instance of the Sidekick
alpha = Sidekick(7,3,10,0.5,[0,0],[90,178],[119.484,171.701])

# On startup, homes position
alpha.initialize()


# Dictionary of available commands
comdict = {
        "initialize" : alpha.initialize,
        "hardware check" : alpha.hardwarecheck,
        "xy position" : alpha.print_current_xy,
        "angular position" : alpha.print_angular_position,
        "free move" : alpha.freemove,
        "sleep" : alpha.release,
        "wake" : alpha.wake,
        "return home" : alpha.return_home,
        "manual purge" : alpha.manualpurge,
        "remap" : alpha.remap,
        "set purge" : alpha.purgeset,
        "execute saved protocol" : alpha.execute_protocol,
        "g28" : alpha.return_home,  # G-CODE equivalent comamnds
        "g29" : alpha.remap,
        "m17" : alpha.wake,
        "m18" : alpha.release,
        "m24" : alpha.execute_protocol
        }

# Main loop, awaiting command

while True:
    # Get User Input
    command = input("awaiting command\n")
    command = command.lower()
    
    if command in comdict:  # handle simple commands without arguments
        comdict[command]()
    elif command == "":     # handle blank line
        continue
    else:
        if command[0]=="p":   # interpret it as our own simplified command type
            pumpid, wellid, volume = com_parser(command)
            alpha.movetowell(pumpid,wellid)
            alpha.dispense(pumpid,volume)
        elif command[0]=="g":  # interpret it as gcode
            x, y, volumes = gcode_parser(command)
            
            #print([x,y])
            # if x or y (or both) are not specified by G-Code, then use the current value
            currentXY = alpha.current_xy()
           
            if x is None:  
                x = currentXY[0]
            if y is None:
                y = currentXY[1]

            # move to desired position
            alpha.movetoXY("center", x, y)

            # perform dispense for each pump in order 
            # NOTE: This is probably not the desired operation, as it will dispense from these pumps with the 
            #       center defined as above, rather than with the given pump output in that location.
            
            if volumes is not None:
                for (i,v) in enumerate(volumes):
                    pumpid = "p"+str(i+1)
                    alpha.dispense(pumpid, v)
        

            
```

### parser.py

```python

def gcode_parser(command):
    """Parse Gcode commands"""
    x = None
    y = None
    volumes = None

    tokens = command.split()
    tokens.reverse()

    #print(tokens)
    cmd = tokens.pop()

    if cmd != "g0":
        print("error:  gcode command ", cmd, "is not supported.  Only G0 based moves are supported.")
        return [x, y, volumes]
    
    while (tokens):
        cmd = tokens.pop()

        if cmd == "x": # handle space between X and input
            x = float(tokens.pop())/10.
        elif cmd[0] == "x": #handle no space after x
            x = float(cmd[1:])/10.  # gcode uses units of millimeters, convert to centimeters
        elif cmd == "y":
            y = float(tokens.pop())/10.
        elif cmd[0] == "y":
            y = float(cmd[1:])/10.
        elif cmd == "e":
            volumes = [float(v) for v in tokens.pop().split(";")] # assume uL units
        elif cmd[0] == "e":
            volumes = [float(v) for v in cmd[1:].split(";")]

    return [x, y, volumes]


def com_parser (command):
    """Parse the movement or dispense command string."""
    
    tokens = command.split()

    # Indicated Pump
    pumpid = tokens[0]
    
    # Target Well
    try:
        wellid = tokens[1]
    except:
        wellid = []
    
    # Target Volume
    if len(tokens) == 3:
        try:
            volume = float(tokens[2])
        except:
            print("Volume (microliters) not recognized, please enter in a numerical value")
            volume = 0
    else:
        volume = 0
    
    return [pumpid,wellid,volume]

```

### plategen.py

```python
import kinematicsfunctions as kf

# This function interpolates the remaining well locations from the four corner wells. Used when setting up a new plate, or if the Sidekick is plating inaccurately.
def remap_plate(A1,A12,H1,H12,L1,L2,L3,origin):
    """Given the four corner wells and the Sidekick dimensions, interpolate the other well locations"""
    def linear_interpolate(startwell,endwell,wells):
        """Interpolates the coordinates between a given start well, and end well."""
        
        dist_between_wells_x = (endwell[0] - startwell[0])/ (wells-1)
        dist_between_wells_y = (endwell[1] - startwell[1]) / (wells-1)

        final_coordinates = [[startwell[0] + i * dist_between_wells_x, startwell[1] + i * dist_between_wells_y] for i in range(wells)]
        return final_coordinates


    # Calculates the outer edges
    first_col = linear_interpolate(A1, H1, 8)
    last_col = linear_interpolate(A12, H12,8)
    all_coord = [linear_interpolate(first_col[i], last_col[i], 12) for i in range(len(first_col))]

    # Flattens list
    flattened_coords = [val for sublist in all_coord for val in sublist]

    # Uses inverse kinematics to convert to thetas
    thetas = [kf.inverse_kinematics(L1,L2,L3,origin,flattened_coords[i]) for i in range(len(flattened_coords))]
    theta1 = [thetas[i][0] for i in range(len(thetas))]
    theta2 = [thetas[i][1] for i in range(len(thetas))]

    # Fills well ID list
    row = ["a","b","c","d","e","f","g","h"]
    column = list(map(str, list(range(1,13))))
    wellids = [row[i] + column[j] for i in range(len(row)) for j in range(len(column))]
    
    return [theta1,theta2,wellids]

```

## tests

### __init__.py

```python

```

## tests\hardware

### __init__.py

```python

```

### test_firmware_integration.py

```python
import unittest
import time
import json

# Import necessary classes from your project
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message
from adafruit_board_toolkit.circuitpython_serial import data_comports

# --- Test Configuration ---
# Timeout for waiting for a response from the device, in seconds.
# The device sends a heartbeat every 5s, so this should be longer than that.
DEVICE_RESPONSE_TIMEOUT = 7 

def find_device_port():
    """Scans for and returns the first available CircuitPython data port."""
    ports = data_comports()
    return ports[0].device if ports else None

# Get the device port once when the module is loaded.
# This is a condition for running the tests in this class.
DEVICE_PORT = find_device_port()

@unittest.skipIf(DEVICE_PORT is None, "Hardware Test: No CircuitPython device found.")
class TestFakeFirmwareIntegration(unittest.TestCase):
    """
    An integration test case that communicates with a live microcontroller
    running the 'fake' firmware.
    
    This is NOT a pure unit test. It requires:
    1. A CircuitPython board to be physically connected via USB.
    2. The 'fake' firmware to be loaded and running on the board.
    """

    def setUp(self):
        """
        This method runs before each test. It finds the device and
        opens the serial connection.
        """
        self.assertIsNotNone(DEVICE_PORT, "setUp failed: Device port should not be None.")
        
        postman_params = {
            "port": DEVICE_PORT,
            "baudrate": 115200,
            "timeout": 0.1,  # Non-blocking timeout
            "protocol": "serial"
        }
        self.postman = SerialPostman(postman_params)
        self.postman.open_channel()
        
        # Give the connection a moment to establish
        time.sleep(1)
        
        # Flush any old data from the device's serial buffer
        # The channel is the underlying pyserial object
        self.postman.channel.reset_input_buffer()
        print(f"\nConnected to {DEVICE_PORT}...")

    def tearDown(self):
        """
        This method runs after each test. It ensures the serial
        connection is closed.
        """
        if self.postman and self.postman.is_open:
            self.postman.close_channel()
            print("Disconnected.")

    def _listen_for_message(self, target_status: str, timeout: float) -> Message | None:
        """Helper function to listen for a specific message type within a timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            raw_data = self.postman.receive()
            if raw_data:
                try:
                    message = Message.from_json(raw_data)
                    print(f"  - Received: [{message.status}]")
                    if message.status == target_status:
                        return message
                except (json.JSONDecodeError, ValueError):
                    print(f"  - Received unparseable data: {raw_data}")
            time.sleep(0.1) # Don't spam the CPU
        return None

    def test_01_receive_heartbeat(self):
        """
        Verify that the host can receive an unsolicited HEARTBEAT message.
        """
        print("--- Test: Receiving HEARTBEAT ---")
        print(f"Listening for up to {DEVICE_RESPONSE_TIMEOUT} seconds...")
        
        heartbeat_msg = self._listen_for_message("HEARTBEAT", DEVICE_RESPONSE_TIMEOUT)
        
        self.assertIsNotNone(heartbeat_msg, f"Did not receive a HEARTBEAT within {DEVICE_RESPONSE_TIMEOUT}s.")
        self.assertEqual(heartbeat_msg.subsystem_name, "FAKE")
        self.assertIn("analog_value", heartbeat_msg.payload)
        self.assertIsInstance(heartbeat_msg.payload["analog_value"], int)

    def test_02_send_blink_and_get_success(self):
        """
        Verify that the host can send an INSTRUCTION and receive a SUCCESS response.
        """
        print("--- Test: Send BLINK, receive SUCCESS ---")
        
        # 1. Arrange: Create the blink command
        blink_payload = {"func": "blink", "args": ["2"]} # Blink twice
        blink_message = Message.create_message(
            subsystem_name="HOST",
            status="INSTRUCTION",
            payload=blink_payload
        )

        # 2. Act: Send the command
        print(f"Sending INSTRUCTION: {blink_message.to_dict()}")
        self.postman.send(blink_message.serialize())
        
        # 3. Assert: Listen for the SUCCESS response
        print(f"Listening for SUCCESS response for up to {DEVICE_RESPONSE_TIMEOUT} seconds...")
        success_msg = self._listen_for_message("SUCCESS", DEVICE_RESPONSE_TIMEOUT)

        self.assertIsNotNone(success_msg, f"Did not receive a SUCCESS response within {DEVICE_RESPONSE_TIMEOUT}s.")
        self.assertEqual(success_msg.subsystem_name, "FAKE")
        self.assertIn("Completed 2 blinks", success_msg.payload.get("detail", ""))


if __name__ == '__main__':
    unittest.main()
```

## tests\host_app

### __init__.py

```python

```

### test_fake_device.py

```python
# tests/host_app/test_fake_device.py
import unittest
from host_app.devices.fake_device import FakeDevice
from shared_lib.messages import Message
import json

class TestFakeDevice(unittest.TestCase):

    def setUp(self):
        self.fake_device = FakeDevice("TestFakeDevice")

    def tearDown(self):
        self.fake_device.stop()

    def test_initialization(self):
        self.assertIsNotNone(self.fake_device.secretary)
        self.assertTrue(self.fake_device.secretary.running)
        self.assertEqual(self.fake_device.secretary.name, "TestFakeDevice_Secretary")

    def test_send_and_receive_instruction(self):
        # 1. Host sends an instruction to the fake device
        instruction_payload = {"func": "set_led", "args": ["on"]}
        self.fake_device.send_command(instruction_payload)

        # 2. FIX: Allow the fake device's secretary to process the incoming message over several cycles.
        #    A single update is not enough for Monitoring -> Reading -> Routing -> Filing -> Monitoring -> Sending.
        for _ in range(5):
            self.fake_device.update()

        # 3. Check what the fake device "sent back" (stored in its DummyPostman's sent_values)
        responses = self.fake_device.get_sent_by_fake_device()

        self.assertEqual(len(responses), 1, "Should have received exactly one response.")
        response_message = responses[0]

        self.assertEqual(response_message.subsystem_name, "TestFakeDevice")
        self.assertEqual(response_message.status, "SUCCESS")
        # Payload is a dict, so we need to compare dicts
        self.assertEqual(response_message.payload, {"status": "LED set to on"})

    def test_unknown_instruction(self):
        instruction_payload = {"func": "do_something_unknown"}
        self.fake_device.send_command(instruction_payload)

        # FIX: Also requires multiple updates
        for _ in range(5):
            self.fake_device.update()

        responses = self.fake_device.get_sent_by_fake_device()
        self.assertEqual(len(responses), 1)
        response_message = responses[0]

        self.assertEqual(response_message.subsystem_name, "TestFakeDevice")
        self.assertEqual(response_message.status, "PROBLEM")
        self.assertIn("error", response_message.payload)


    def test_multiple_messages(self):
        # Send a few commands
        self.fake_device.send_command({"func": "set_led", "args": ["on"]})
        self.fake_device.send_command({"func": "set_led", "args": ["off"]})

        # Process multiple times. Need more updates for more messages.
        for _ in range(10):
            self.fake_device.update()

        responses = self.fake_device.get_sent_by_fake_device()
        self.assertEqual(len(responses), 2)

        self.assertEqual(responses[0].payload, {"status": "LED set to on"})
        self.assertEqual(responses[1].payload, {"status": "LED set to off"})

if __name__ == '__main__':
    unittest.main()
```

