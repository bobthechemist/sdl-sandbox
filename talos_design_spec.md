# Talos-SDL Instrument Design Specification: BUZZER_V1

This document was generated interactively using the Socratic method.

## 1. High-Level Definition
*   **Primary Purpose:** Initialize the I2C connection
*   **Primary Actions:** turn on motor, turn off motor, change motor effect
*   **Telemetry Outputs:** Is the motor active?
*   **Failure Conditions:** none
*   **AI Agent Operational Guidance:** none

## 2. Hardware Configuration (`SUBSYSTEM_CONFIG`)
### GPIO Pin Mapping
No custom pins defined (uses standard serial or defaults).

### Operational Parameters & Settings
| Parameter Name | Default Value |
| :--- | :--- |
| effect: an integer from 0 to 123 | 64 |

### Safety & Guard Limits
| Boundary Name | Value Limit |
| :--- | :--- |
| max_effect | 123 |
| min_effect | 0 |

## 3. Command Interface (The API)
### Command: `motor_on`
*   **Description:** turns on the buzzing motor
*   **AI Agent Accessible:** `True`
*   **Success Metric:** returns a SUCCESS message
*   **Command Guards:** none
*   **Arguments:**
    *   None

### Command: `motor_off`
*   **Description:** turns motor off
*   **AI Agent Accessible:** `True`
*   **Success Metric:** Returns a SUCCESS message
*   **Command Guards:** none
*   **Arguments:**
    *   None

### Command: `set_effect`
*   **Description:** Changes the effect value for the motor buzzing (0 to 123)
*   **AI Agent Accessible:** `True`
*   **Success Metric:** Returns a SUCCESS message
*   **Command Guards:** motor must be off
*   **Arguments:**
    *   `effect` (int) (Default: 64)

## 4. State Machine Custom States
### State: `Initialize`
*   **Single Responsibility:** Initialize the I2C connection
*   **Entry Actions (`enter()`):** Set up the I2C connection, connect the adafruit_drv2605 and set the default effect by setting .sequence[0]
*   **Internal Operations (`update()`):** none
*   **Transition & Exit Events:** no communication failures, transitions to idle
*   **Exit Cleanup Actions (`exit()`):** none

