import pandas as pd
import numpy as np

# --- Configuration ---
# The name of your data file
CSV_FILENAME = 'pump_calibration_251029.csv'

# Density of water in g/mL (or mg/µL). Adjust for your lab's temperature.
# 0.998 g/mL is a good approximation for ~22°C (72°F).
WATER_DENSITY = 0.998

# --- Analysis ---

try:
    # 1. Load the data from the CSV file
    data = pd.read_csv(CSV_FILENAME)
    print(f"Successfully loaded data from '{CSV_FILENAME}'.\n")
except FileNotFoundError:
    print(f"Error: The file '{CSV_FILENAME}' was not found.")
    print("Please make sure the script and the CSV file are in the same directory.")
    exit()

# 2. Construct the Design Matrix 'A' (in units of 10 µL steps)
# The CSV file has commanded volumes (e.g., 900 µL), but our model is based
# on the number of 10 µL increments (steps). So, we divide by 10.
pump_columns = ['p1', 'p2', 'p3', 'p4']
A = data[pump_columns].values / 10.0

# 3. Construct the Measurement Vector 'b' (in total µL)
# The 'mass' column is in grams. We convert it to volume in microliters (µL).
# Volume (µL) = Mass (g) / Density (g/mL) * 1000 (µL/mL)
mass_grams = data['mass'].values
b = (mass_grams / WATER_DENSITY) * 1000

# 4. Solve the overdetermined system Ax = b using least squares
# This finds the vector 'x' that minimizes the squared difference between Ax and b.
# 'x' will contain our four calibration constants (c1, c2, c3, c4).
try:
    solution, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
except np.linalg.LinAlgError as e:
    print(f"Linear algebra error: {e}")
    print("This can happen if the columns of the design matrix are not linearly independent.")
    exit()

# --- Results & Statistics ---

print("--- Pump Calibration Results ---")
print("The calibration factor is the actual average volume dispensed per commanded 10 µL step.\n")

for i, cal_factor in enumerate(solution):
    pump_num = i + 1
    # Calculate percentage error relative to the nominal 10 µL
    percent_error = ((cal_factor - 10.0) / 10.0) * 100
    print(f"Pump {pump_num}: {cal_factor:.4f} µL / step  (Error: {percent_error:+.2f}%)")

print("\n--- Experiment Fit Statistics ---")
print("This shows how well the calculated model fits your actual measurements.\n")

# Calculate the model's predicted volumes and masses for each experiment
predicted_volumes_uL = A @ solution
predicted_masses_g = (predicted_volumes_uL / 1000) * WATER_DENSITY

# Display the error (residual) for each measurement
print("Exp # | Measured Mass (g) | Predicted Mass (g) | Error (mg)")
print("------|-------------------|--------------------|------------")
for i in range(len(mass_grams)):
    error_mg = (mass_grams[i] - predicted_masses_g[i]) * 1000
    print(f"  {i+1: <4}|      {mass_grams[i]:.4f}      |       {predicted_masses_g[i]:.4f}       |  {error_mg:+.2f}")

# Calculate the overall model error
# The sum of squared residuals is returned by the lstsq function in units of (µL^2)
sum_of_squared_residuals = residuals[0]
num_experiments = len(b)
# RMSE gives the typical error magnitude in µL
rmse_volume = np.sqrt(sum_of_squared_residuals / num_experiments)

print("\n--- Overall Model Quality ---")
print(f"Root Mean Square Error (RMSE): {rmse_volume:.4f} µL")
print("This value represents the typical deviation of the model's prediction from your measured data.")