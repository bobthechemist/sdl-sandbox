import numpy as np
import json
from pathlib import Path
import sys

# Define the Project Root to save the file in the right place
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- 1. INPUT DATA ---
# Using the Local Coordinate System: A1 = (0, 0)
# X axis = Rows (A->H), Y axis = Columns (1->12)
# Units: cm

# Measured Joint Coordinates [M1, M2]
# Order: A1, H1, H12, A12
steps_data = np.array([
    [354, 909],   # A1
    [112, 1199],  # H1
    [469, 1523],  # H12
    [937, 1458]   # A12
])

# Theoretical Plate Coordinates [x, y]
# Pitch = 0.9 cm
# A->H = 7 steps * 0.9 = 6.3 cm
# 1->12 = 11 steps * 0.9 = 9.9 cm
xy_data = np.array([
    [0.0, 0.0],   # A1
    [6.3, 0.0],   # H1
    [6.3, 9.9],   # H12
    [0.0, 9.9]    # A12
])

def main():
    print("--- Generating Calibration Coefficients ---")
    
    # --- 2. CONSTRUCT DESIGN MATRIX ---
    # We fit a quadratic model: Steps = C0 + C1*x + C2*y + C3*x^2 + C4*x*y + C5*y^2
    x = xy_data[:, 0]
    y = xy_data[:, 1]
    
    # Stack features into columns
    A = np.column_stack([
        np.ones_like(x), # 1 (Bias)
        x,               # x
        y,               # y
        x*y,             # xy
    ])

    # --- 3. SOLVE FOR COEFFICIENTS ---
    # We solve Ax = B for Motor 1 and Motor 2 simultaneously
    # lstsq finds the solution that minimizes the error
    coeffs_m1, resid_m1, _, _ = np.linalg.lstsq(A, steps_data[:, 0], rcond=None)
    coeffs_m2, resid_m2, _, _ = np.linalg.lstsq(A, steps_data[:, 1], rcond=None)

    print("\nMotor 1 Coefficients:", coeffs_m1)
    print("Motor 2 Coefficients:", coeffs_m2)

    # --- 4. VALIDATION ---
    print("\n--- Model Verification ---")
    print(f"{'Well':<5} | {'Measured (M1, M2)':<20} | {'Predicted (M1, M2)':<20} | {'Error':<20}")
    print("-" * 75)
    
    wells = ["A1", "H1", "H12", "A12"]
    for i in range(len(xy_data)):
        # Predict using dot product
        # features: [1, x, y, xy]
        features = A[i] 
        pred_m1 = np.dot(features, coeffs_m1)
        pred_m2 = np.dot(features, coeffs_m2)
        
        meas_m1, meas_m2 = steps_data[i]
        
        err_m1 = meas_m1 - pred_m1
        err_m2 = meas_m2 - pred_m2
        
        print(f"{wells[i]:<5} | {meas_m1:4d}, {meas_m2:4d}          | {pred_m1:7.1f}, {pred_m2:7.1f}      | {err_m1:5.1f}, {err_m2:5.1f}")

    # --- 5. EXPORT JSON ---
    output_data = {
        "calibration_date": "2026-01-30",
        "method": "4_point_bilinear_plate_relative",
        "description": "Maps plate-relative cm (A1=0,0) to absolute motor steps.",
        "coefficients": {
            "motor1": coeffs_m1.tolist(),
            "motor2": coeffs_m2.tolist()
        },
        "plate": {
            "well_pitch_cm": 0.9,
            "rows": "ABCDEFGH",
            "columns": 12
        }
    }

    out_path = PROJECT_ROOT / "host" / "calibration" / "quadratic_calibration.json"
    with open(out_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n[SUCCESS] Calibration file saved to:\n {out_path}")
    print("\nNEXT STEP: Copy this file to your Sidekick CIRCUITPY drive.")

if __name__ == "__main__":
    main()