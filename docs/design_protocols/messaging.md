# **Self-Driving Laboratory: Standard Messaging Protocol (Version 1.0)**

## 1. Introduction

This document defines the standard messaging protocol for all communication between the host computer and microcontroller-driven instruments within the Self-Driving Laboratory software stack. Adherence to this standard is mandatory for all new device firmware and is the target for refactoring existing devices.

The primary goals of this protocol are:
*   **Unambiguity:** To ensure that the intent and content of every message are explicit and machine-readable.
*   **Robustness:** To create a system that is resilient to changes and supports optional parameters and future extensibility.
*   **Scalability:** To provide a single, unified framework that supports both direct user control (Human-in-the-Loop) and advanced automation (Autonomous).

## 2. Core Message Structure

All messages, regardless of direction or purpose, MUST be serialized JSON objects adhering to the following structure:

| Key              | Type    | Description                                                                 |
| ---------------- | ------- | --------------------------------------------------------------------------- |
| `timestamp`   | Integer | The sender's timestamp of message creation in seconds time.time().               |
| `subsystem_name` | String  | The name of the subsystem sending the message (e.g., "HOST", "RoboticArm-Sidekick"). |
| `status`         | String  | The status of the message. MUST be one of the types defined in Section 3. |
| `meta`           | Object  | Reserved JSON object |
| `payload`        | Object  | A JSON object containing the message's specific content. See Section 4.   |

**Example of a base message:**
```json
{
  "timestamp": 1678890000000,
  "subsystem_name": "HOST",
  "status": "INSTRUCTION",
  "payload": { ... }
}
```

## 3. Message Status Definitions

The `status` field is the primary indicator of a message's purpose.

| Status            | Direction        | When to use                                                                      |
| ----------------- | ---------------- | -------------------------------------------------------------------------------- |
| **`INSTRUCTION`** | Host -> Device   | To command a device to perform an action.                                        |
| **`SUCCESS`**     | Device -> Host   | To acknowledge the successful completion of an `INSTRUCTION` that does not return data. |
| **`PROBLEM`**     | Device -> Host   | To indicate that an `INSTRUCTION` failed or an error occurred.                     |
| **`DATA_RESPONSE`** | Device -> Host   | To send **solicited data** in direct response to an `INSTRUCTION`.                  |
| **`TELEMETRY`**   | Device -> Host   | To send **unsolicited data**, such as periodic sensor readings or status updates. |
| **`WARNING`**     | Device <-> Host  | For non-critical issues or alerts.                                               |
| **`INFO`**        | Device <-> Host  | For human-readable, informational text (e.g., boot messages, state changes).      |
| **`DEBUG`**       | Device <-> Host  | For verbose debugging information not intended for production use.                |

## 4. Payload Schema Specifications

The structure of the `payload` object is strictly defined based on the message `status`.

### 4.1. Instruction Payload (`status: "INSTRUCTION"`)

Used to command a device.

*   `func` (String): The name of the function to be executed on the device.
*   `args` (Object): A JSON object containing the parameters for the function. **This MUST be an object (dictionary) of named arguments, not an array (list) of positional arguments.**

**Example:**
```json
// GOOD: Robust and clear
{
  "func": "move_relative",
  "args": {
    "x_dist": 100,
    "y_dist": 50,
    "speed": 25
  }
}

// BAD: Ambiguous and fragile - DO NOT USE
{
  "func": "move_relative",
  "args": [100, 50, 25]
}
```

### 4.2. Data Payload (`status: "DATA_RESPONSE"` or `"TELEMETRY"`)

**NOTE** Requirements for metadata may be overkill. 

Used for all messages that contain structured, machine-readable data. The payload MUST contain two top-level keys: `metadata` and `data`.

*   **`metadata`** (Object): An object describing the data.
    *   `data_type` (String): A unique, descriptive name for the type of data (e.g., "spectrum", "xy_coordinates", "image_base64").
    *   `timestamp` (Integer, Optional): Appropriate timestamp for **data acquisition** (messaging already has a timestamp).
    *   `units` (Object, Optional): A key-value map defining the units of the data fields (e.g., `{"wavelength": "nm", "intensity": "counts"}`).
    *   `source_instruction_id` (String, Optional): A unique identifier that can be used to correlate a `DATA_RESPONSE` with its originating `INSTRUCTION`.

*   **`data`** (Object | Array): The actual data being transmitted. The structure is dependent on the `data_type` defined in the metadata.

**Example:**
```json
{
  "metadata": {
    "data_type": "spectrum",
    "timestamp": 1678890000123456,
    "units": {
      "wavelength": "nm",
      "intensity": "counts"
    }
  },
  "data": {
    "wavelength": [400.1, 400.5, 401.0],
    "intensity": [1024, 1030, 1055]
  }
}
```

## 5. Standard Call and Response Examples

### 5.1. Scenario 1: Simple Command (No Data Return)

Host commands an LED to blink.

**Host -> Device (`INSTRUCTION`)**
```json
{
  "timestamp": 1678890100000,
  "subsystem_name": "HOST",
  "status": "INSTRUCTION",
  "payload": {
    "func": "blink",
    "args": {
      "count": 3,
      "on_time": 1
    }
  }
}
```

**Device -> Host (`SUCCESS`)**
```json
{
  "timestamp": 1678890100800,
  "subsystem_name": "Generic-MCU",
  "status": "SUCCESS",
  "payload": {
    "message": "Blink command executed."
  }
}
```

### 5.2. Scenario 2: Command with Data Return

Host commands a spectrometer to perform a measurement.

**Host -> Device (`INSTRUCTION`)**
```json
{
  "timestamp": 1678890200000,
  "subsystem_name": "HOST",
  "status": "INSTRUCTION",
  "payload": {
    "func": "measure_spectrum",
    "args": {
      "integration_time_ms": 100
    }
  }
}
```

**Device -> Host (`DATA_RESPONSE`)**
```json
{
  "timestamp": 1678890200150,
  "subsystem_name": "EndEffector-Spectrometer",
  "status": "DATA_RESPONSE",
  "payload": {
    "metadata": {
      "data_type": "spectrum",
      "timestamp": 1678890200123456,
      "units": {"wavelength": "nm", "intensity": "counts"}
    },
    "data": {
      "wavelength": [400.1, 400.5, ...],
      "intensity": [1024, 1030, ...]
    }
  }
}
```

### 5.3. Scenario 3: Unsolicited Telemetry

Device periodically sends its internal temperature.

**Device -> Host (`TELEMETRY`)**
```json
{
  "timestamp": 1678890300000,
  "subsystem_name": "RoboticArm-Sidekick",
  "status": "TELEMETRY",
  "payload": {
    "metadata": {
      "data_type": "temperature",
      "timestamp": 1678890300000000,
      "units": {"temp": "celsius"}
    },
    "data": {
      "temp": 42.5
    }
  }
}
```