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


