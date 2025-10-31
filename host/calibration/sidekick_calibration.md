# Sidekick Calibration

This directory contains scripts for calibrating the Sidekick robotic arm. The current and official method uses a 9-point quadratic surface fit to map well plate coordinates directly to motor steps.

**NOTE**: These calibration routines should be considered work in progress. The present version of the firmware (2025-10-31) does not use the quadratic calibration and instead uses a similarity (translation, rotation, scaling) transform just to align the well plates. More needs to be done to identify a robust calibration approach.

## Official Calibration Process

The calibration process is now streamlined into two main steps:

### Step 1: Generate Calibration Data

1.  Connect the Sidekick device to the host computer.
2.  Run the main calibration wizard from the project's root directory:
    ```bash
    python -m host.calibration.run_quadratic_calibration
    ```
3.  The script will guide you through an interactive process to locate 9 key wells on the 96-well plate (`A1`, `A6`, `A12`, `E1`, etc.). Use the `W/A/S/D` keys to jog the motors and `T` to change the step size.
4.  Upon completion, the script will perform a quadratic least-squares fit and save the resulting coefficients to `host/calibration/quadratic_calibration.json`.

### Step 2: Deploy to Device

1.  **Manually copy** the generated `quadratic_calibration.json` file from the `host/calibration/` directory to the root of the Sidekick's `CIRCUITPY` USB drive.
2.  Reset the Sidekick. On boot, the firmware will automatically load this file to enable accurate `to_well` positioning.

### Step 3 (Optional): Verify the Calibration

You can test the new calibration file without dispensing by using the verification script:

```bash
python -m host.calibration.verify_calibration
```

This script will load the same JSON file, prompt you for any well designation (e.g., "B7", "G11"), and command the robot to move there. This allows you to visually inspect the accuracy across the entire plate.

---

## Archived Calibration Methods

During development, several other calibration strategies were explored. While they have been superseded by the quadratic fit method, the knowledge gained from them is preserved here for historical context.

*   **`calibrate_fivebar.py`**:
    *   **Goal:** To solve the classic robotics problem of finding the true physical parameters of the five-bar linkage (i.e., the exact lengths of `L1`, `L2`, `L3`, `Ln`).
    *   **Method:** It used data from `diagnose_motor_steps.py` and applied a non-linear least-squares optimization (`scipy.optimize.least_squares`) to fit the forward kinematics model to the measured data.
    *   **Outcome:** This analytical approach is powerful but proved to be overly sensitive to small physical non-idealities not captured in the model (e.g., joint-arm alignment, non-perfect planarity). The direct quadratic mapping proved more robust for this specific hardware.

*   **`run_sidekick_calibration.py` (Angle-Based):**
    *   **Goal:** To create a correction map for the motor *angles* instead of the final XY coordinates.
    *   **Method:** The user would jog the arm in Cartesian space (cm units). The script would record the device's *predicted* motor angles and the *actual* motor angles and compute an affine transformation matrix to correct the angles.
    *   **Outcome:** This was an intermediate step but still relied on the underlying (and slightly flawed) inverse kinematics model. Correcting the final output (motor steps) directly was more effective.

*   **`sidekick_calibration_data.py` (3-Point Affine Transform):**
    *   **Goal:** To create a simple linear (affine) transformation from XY coordinates to motor steps.
    *   **Method:** It used only 3 points (A1, H1, H12) to solve for a 2x3 transformation matrix.
    *   **Outcome:** This worked reasonably well but was not as accurate as the quadratic model, which better captures the non-linear nature of the SCARA arm's movement.

*   **`diagnose_motor_steps.py`**:
    *   **Goal:** A data-gathering script specifically for `calibrate_fivebar.py`.
    *   **Method:** It moved to a well, recorded the initial steps, and then allowed the user to jog to the correct position using direct motor step commands.
    *   **Outcome:** Its interactive motor jogging (`W/A/S/D`) was very effective and has been integrated into the new `run_quadratic_calibration.py` script.
