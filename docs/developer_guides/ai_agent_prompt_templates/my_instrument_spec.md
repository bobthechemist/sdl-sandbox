# Talos Instrument Spec Sheet: [Instrument Name]

## 1. Overview & Hardware
*   **Subsystem Name:** `[e.g., STIR_PLATE, SMART_VALVE, TEMP_SENSOR]`
*   **Primary Purpose:** [What does this instrument do in one or two sentences?]
*   **Hardware Components Used:** 
    *   [e.g., 1x Adafruit MotorKit FeatherWing]
    *   [e.g., 1x DS18B20 Temperature Sensor]
    *   [e.g., 1x Standard Hobby Servo]
*   **AI Guidance:** [What does the AI agent need to know to use this safely? E.g., "The heater must be turned on before dispensing."]

## 2. Configuration & Wiring (`SUBSYSTEM_CONFIG`)
*List the physical pins and default settings the AI should use to write the configuration dictionary.*

**Pins:**
*   `[e.g., servo_pin]`: `[e.g., board.GP15]`
*   `[e.g., sensor_sda]`: `[e.g., board.SDA]`
*   `[e.g., sensor_scl]`: `[e.g., board.SCL]`

**Operational Parameters & Safe Limits:**
*   `[e.g., default_speed]`: `[e.g., 0.5]`
*   `[e.g., max_temperature]`: `[e.g., 85.0]`
*   `[e.g., servo_closed_angle]`: `[e.g., 0]`
*   `[e.g., servo_open_angle]`: `[e.g., 90]`

## 3. Telemetry & Status Data
*What data should this instrument report back to the host computer?*
*   **Telemetry (Streams constantly in the background):** [e.g., Current temperature, current motor speed]
*   **Status (Sent when requested via `get_info`):** [e.g., Is the heater currently on? What is the current servo angle?]

## 4. Commands (The API)
*What commands can the user or AI issue to control this device? Add rows as needed.*

| Command Name | Description | Arguments (Name: Type) | What happens? (Success Condition) |
| :--- | :--- | :--- | :--- |
| `[e.g., open_valve]` | [Opens the servo valve completely.] | [None] | [Servo moves to 90 degrees, returns SUCCESS.] |
| `[e.g., set_speed]` | [Sets the speed of the motor.] | `speed`: float (0.0 to 1.0) | [Motor speed updates, returns SUCCESS.] |
| `[e.g., read_temp]` | [Reads the current liquid temp.]| [None] | [Returns a DATA_RESPONSE with the temperature in Celsius.] |

## 5. Operating States (The State Machine)
*Talos instruments run on a State Machine. The agent will automatically build an `Initialize` state (to set up your hardware), an `Idle` state (to wait for commands), and an `Error` state.* 

**Do you need custom states?**
*   *If your device just reads sensors or flicks switches instantly, you **do not** need custom states. (Leave this section blank).*
*   *If your device does something that takes time (like "Heating up to a target temperature" or "Moving a robotic arm to a coordinate"), define that state below.*

**Custom State: `[e.g., Heating]`**
*   **Purpose:** [e.g., To safely apply power to the heater until the target temperature is reached.]
*   **What triggers it:** [e.g., The `set_temperature` command.]
*   **What happens in the loop:** [e.g., Constantly checks the temperature. If it hits the target, turns off the heater and goes back to Idle. If it exceeds `max_temperature`, goes to Error.]