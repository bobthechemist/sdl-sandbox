import numpy as np
from scipy.optimize import least_squares
import math

# ==========================================
# 1. SETUP ROBOT CONSTANTS (YOU MUST EDIT THESE)
# ==========================================
# Arm lengths (mm)
L1 = 70.0  # Proximal arm (motor to elbow)
L2 = 1100.0  # Distal arm (elbow to end effector)
# Base separation (mm) - Distance between motor shafts
D_model = 0.0 
# Motor resolution
STEPS_PER_REV = 360 *0.9 * 8 # e.g., 200 step motor * 16 microstepping
STEPS_PER_DEG = STEPS_PER_REV / 360.0

# ==========================================
# 2. INPUT DATA (FROM YOUR TABLE)
# ==========================================
# We need the Known Cartesian (X,Y) of the wells. 
# Since you didn't provide X,Y, we will REVERSE CALCULATE them 
# from your "Predicted" steps assuming your original kinematics were "perfect".
# If you have the actual mm coordinates of A1, H1, etc., replace `target_coords` below.

data = [
    # (m1_act, m2_act, m1_pred, m2_pred)
    (366, 892,  335, 887),   # A1
    (137, 1171, 131, 1178),  # H1
    (564, 1116, 552, 1113),  # C5
    (543, 1306, 546, 1308),  # F8
    (971, 1469, 987, 1486),  # A12
    (501, 1510, 518, 1516)   # H12
]

# ==========================================
# 3. KINEMATICS FUNCTIONS
# ==========================================
def forward_kinematics(steps1, steps2, d_val, offset1, offset2):
    """
    Calculates X,Y based on steps, effective base distance, and angular offsets.
    Assumes standard 5-bar (adjust geometry math if yours is non-standard).
    """
    # Convert steps to radians, adding the optimization offset
    theta1 = math.radians((steps1 / STEPS_PER_DEG) + offset1)
    theta2 = math.radians((steps2 / STEPS_PER_DEG) + offset2)
    
    # Locations of the "elbows"
    # Assuming M1 is at (-d/2, 0) and M2 is at (d/2, 0)
    # Adjust this logic to match your specific coordinate frame definition
    x1 = -d_val/2 + L1 * math.cos(theta1)
    y1 = L1 * math.sin(theta1)
    
    x2 = d_val/2 + L1 * math.cos(theta2)
    y2 = L1 * math.sin(theta2)
    
    # Distance between elbows
    dist_elbows = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
    # Intersection of distal arms (Circle-Circle intersection)
    # If un-solvable (arms can't reach), return a large error penalty
    if dist_elbows > (L2 + L2) or dist_elbows == 0:
        return 99999.0, 99999.0

    # Math for intersection of two circles
    a = (L2**2 - L2**2 + dist_elbows**2) / (2 * dist_elbows)
    h = math.sqrt(max(0, L2**2 - a**2))
    
    x2_prime = x2 - x1
    y2_prime = y2 - y1
    
    x3 = x1 + a * (x2_prime / dist_elbows) + h * (y2_prime / dist_elbows) # Switch + to - for elbow flip
    y3 = y1 + a * (y2_prime / dist_elbows) - h * (x2_prime / dist_elbows) # Switch - to + for elbow flip
    
    return x3, y3

# Generate "Truth" Targets based on Pred steps (assuming model D and 0 offset)
targets = []
for _, _, p1, p2 in data:
    tx, ty = forward_kinematics(p1, p2, D_model, 0, 0)
    targets.append((tx, ty))

# ==========================================
# 4. OPTIMIZATION ROUTINE
# ==========================================
def error_function(params):
    """
    params[0]: Offset Angle M1 (degrees)
    params[1]: Offset Angle M2 (degrees)
    params[2]: Effective Base Separation (mm) adjustment
    """
    off1, off2, d_adj = params
    current_d = D_model + d_adj
    
    residuals = []
    
    for i in range(len(data)):
        m1_act, m2_act, _, _ = data[i]
        target_x, target_y = targets[i]
        
        # Calculate where the arm IS using Actual Steps + Optimized Params
        calc_x, calc_y = forward_kinematics(m1_act, m2_act, current_d, off1, off2)
        
        # Calculate distance squared error
        residuals.append(calc_x - target_x)
        residuals.append(calc_y - target_y)
        
    return residuals

# Initial guess: [0 deg offset, 0 deg offset, 0mm base adjustment]
initial_guess = [0.0, 0.0, 0.0]

# Run Solver
res = least_squares(error_function, initial_guess)

# ==========================================
# 5. RESULTS
# ==========================================
print("Optimization Success:", res.success)
print(f"M1 Offset: {res.x[0]:.4f} deg")
print(f"M2 Offset: {res.x[1]:.4f} deg")
print(f"Base Separation Adjustment: {res.x[2]:.4f} mm")
print(f"Effective Base Separation: {D_model + res.x[2]:.4f} mm")