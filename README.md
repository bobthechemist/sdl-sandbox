# The Automated Laboratory Instrument Framework (ALIF)

This project is a comprehensive software framework for creating a **Self-Driving Laboratory**, an automated system where a host computer controls multiple scientific instruments, each powered by a CircuitPython-compatible microcontroller.

At its core, the framework uses a **host-device architecture**. The host computer runs a central application that sends commands and manages experimental workflows, while each instrument's microcontroller executes firmware to control its specific hardware (motors, pumps, sensors).

Key architectural features include:

*   **State-Machine-Driven Firmware:** Each instrument's firmware is built as a finite state machine, ensuring predictable and robust behavior by preventing conflicting operations.
*   **JSON-Based Messaging:** All communication between the host and devices occurs over a serial connection using a standardized, human-readable JSON protocol.
*   **Centralized Device Management:** On the host side, a `DeviceManager` handles the discovery, connection, and communication for all instruments, providing a unified interface for control scripts and user interfaces.
*   **Model-View-Controller (MVC) Pattern:** The host application is designed with a clear separation of concerns, allowing for flexible user interfaces (like the provided Tkinter GUI) and enabling autonomous control via scripts or AI agents.

The project is designed for extensibility, with clear documentation and design guidelines (`socratic_design_guidelines.md`) to facilitate the rapid integration of new instruments. It also includes tools for deploying firmware and testing, including the ability to interact with "fake" devices for development without physical hardware. Recent development logs indicate ongoing work to refine the host application, improve documentation, and refactor existing instrument scripts to align with the latest architectural patterns.

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