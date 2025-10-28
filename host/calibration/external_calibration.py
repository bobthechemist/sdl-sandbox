import numpy as np
import matplotlib.pyplot as plt
import json

# === Calibration data ===
XY = np.array([
    [0, 0],
    [4.5, 0],
    [9.9, 0],
    [0, 3.6],
    [4.5, 3.6],
    [9.9, 3.6],
    [0, 6.3],
    [4.5, 6.3],
    [9.9, 6.3]
])

steps = np.array([
    [345, 887],
    [717, 1140],
    [967, 1481],
    [243, 1051],
    [504, 1208],
    [679, 1467],
    [116, 1188],
    [353, 1299],
    [478, 1526]
])

# === Build quadratic design matrix ===
x = XY[:, 0]
y = XY[:, 1]
A = np.column_stack([np.ones_like(x), x, y, x**2, x*y, y**2])

# === Solve least squares for each motor ===
coeffs, _, _, _ = np.linalg.lstsq(A, steps, rcond=None)

def predict_steps(x, y):
    """Predict motor steps for new (x, y) using quadratic surface."""
    features = np.column_stack([np.ones_like(x), x, y, x**2, x*y, y**2])
    return features @ coeffs

# === Evaluate model on calibration data ===
pred_steps = predict_steps(x, y)
errors = steps - pred_steps
rms_error = np.sqrt(np.mean(errors**2, axis=0))

print("Quadratic coefficients:\n", coeffs)
print(f"RMS error (motor1, motor2): {rms_error}")

# === Plot measured vs predicted ===
fig, ax = plt.subplots(1, 2, figsize=(10, 5))

# Motor 1
ax[0].scatter(steps[:,0], pred_steps[:,0], color='blue')
ax[0].plot([steps[:,0].min(), steps[:,0].max()],
           [steps[:,0].min(), steps[:,0].max()],
           'k--', lw=1)
ax[0].set_title("Motor 1: Measured vs Predicted")
ax[0].set_xlabel("Measured steps")
ax[0].set_ylabel("Predicted steps")

# Motor 2
ax[1].scatter(steps[:,1], pred_steps[:,1], color='green')
ax[1].plot([steps[:,1].min(), steps[:,1].max()],
           [steps[:,1].min(), steps[:,1].max()],
           'k--', lw=1)
ax[1].set_title("Motor 2: Measured vs Predicted")
ax[1].set_xlabel("Measured steps")
ax[1].set_ylabel("Predicted steps")

plt.tight_layout()
plt.show()

# Optional: print residuals
print("\nResiduals (Measured - Predicted):\n", np.round(errors, 2))

calibration_data = {
    "calibration_date": "2025-10-28",
    "method": "quadratic_xy_to_steps",
    "coefficients": {
        "motor1": coeffs[:,0].tolist(),
        "motor2": coeffs[:,1].tolist()
        },
    "plate": {
        "well_pitch_cm": 0.9,
        "rows": "ABCDEFGH",
        "columns": 12
        }
    }
with open("quadratic_calibration.json", "w") as f:
    json.dump(calibration_data, f, indent=2)
