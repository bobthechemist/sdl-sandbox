# firmware/sidekick/kinematics.py
# Kinematics calculations for the Sidekick SCARA arm.
# Adapted from the original procedural code.
# type: ignore
import math

# ============================================================================
# UTILITY AND CONVERSION FUNCTIONS
# ============================================================================

def steps_to_degrees(machine, m1_steps, m2_steps):
    """Converts absolute motor steps to angles in degrees."""
    cfg = machine.config['motor_settings']
    steps_per_rev = (360 / cfg['step_angle_degrees']) * cfg['microsteps']
    
    theta1 = (m1_steps / steps_per_rev) * 360
    theta2 = (m2_steps / steps_per_rev) * 360
    return theta1, theta2

def degrees_to_steps(machine, theta1, theta2):
    """Converts motor angles in degrees to absolute step counts."""
    cfg = machine.config['motor_settings']
    steps_per_rev = (360 / cfg['step_angle_degrees']) * cfg['microsteps']
    
    m1_steps = int((theta1 / 360) * steps_per_rev)
    m2_steps = int((theta2 / 360) * steps_per_rev)
    return m1_steps, m2_steps

# ============================================================================
# CORE KINEMATICS LOGIC (Adapted from kinematicsfunctions.py)
# ============================================================================

def _find_standard_position_angle(point):
    """Calculates the angle of a vector in a 360-degree system."""
    x, y = point[0], point[1]
    if x == 0:
        return 90 if y > 0 else 270
    
    ref_angle = math.degrees(math.atan(y / x))
    
    if x > 0 and y >= 0: quadrant = 1 # Q1
    elif x < 0 and y >= 0: quadrant = 2 # Q2
    elif x < 0 and y < 0: quadrant = 3 # Q3
    else: quadrant = 4 # Q4

    if quadrant == 1: return ref_angle
    if quadrant == 2 or quadrant == 3: return 180 + ref_angle
    if quadrant == 4: return 360 + ref_angle

def _get_intersections(x0, y0, r0, x1, y1, r1):
    """Calculates the intersection points of two circles."""
    d = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)

    if d > r0 + r1 or d < abs(r0 - r1) or d == 0:
        return None  # No solution

    a = (r0**2 - r1**2 + d**2) / (2 * d)
    h = math.sqrt(r0**2 - a**2)
    x2 = x0 + a * (x1 - x0) / d
    y2 = y0 + a * (y1 - y0) / d

    x3 = x2 + h * (y1 - y0) / d
    y3 = y2 - h * (x1 - x0) / d
    x4 = x2 - h * (y1 - y0) / d
    y4 = y2 + h * (x1 - x0) / d
    return (x3, y3, x4, y4)

def inverse_kinematics(machine, target_x, target_y):
    """
    Calculates the required motor angles (theta1, theta2) to reach a
    Cartesian coordinate (target_x, target_y).
    
    Returns a tuple (theta1, theta2) on success, or None on failure.
    """
    cfg = machine.config['kinematics']
    L1, L2, L3 = cfg['L1'], cfg['L2'], cfg['L3']
    op_limits = machine.config['operational_limits_degrees']

    # The origin is assumed to be (0, 0)
    p4 = (target_x, target_y)
    
    # Find possible locations for joint P1 (elbow of the upper arm)
    p1_intersections = _get_intersections(p4[0], p4[1], L3, 0, 0, L1)
    if p1_intersections is None:
        machine.log.error("IK Error: Target coordinate is physically unreachable.")
        return None

    # Two possible arm conformations exist. We must check which is valid.
    p1a = (p1_intersections[0], p1_intersections[1])
    p1b = (p1_intersections[2], p1_intersections[3])
    
    possible_solutions = []

    for p1 in [p1a, p1b]:
        # Calculate theta1 for this conformation
        theta1 = _find_standard_position_angle(p1)
        
        # Calculate the vector for the lower arm linkage
        p3_vector = (p4[0] - p1[0], p4[1] - p1[1])
        p3_angle = _find_standard_position_angle(p3_vector)
        
        # The joint P2 is parallel to P3, but offset by L2
        # We find its position by moving backwards from the origin along the p3_angle
        p2_x = 0 + L2 * math.cos(math.radians(p3_angle + 180))
        p2_y = 0 + L2 * math.sin(math.radians(p3_angle + 180))
        
        # Calculate theta2 for this conformation
        theta2 = _find_standard_position_angle((p2_x, p2_y))
        
        # Safety Check: Is this solution within operational limits?
        if (op_limits['m1_min'] <= theta1 <= op_limits['m1_max'] and
            op_limits['m2_min'] <= theta2 <= op_limits['m2_max']):
            possible_solutions.append((theta1, theta2))

    if not possible_solutions:
        machine.log.error("IK Error: All solutions violate operational angle limits.")
        return None
    
    # If multiple solutions are valid, prefer the first one (elbow-back).
    # More advanced logic could choose the one requiring less travel.
    return possible_solutions[0]

def forward_kinematics(machine, theta1, theta2):
    """
    Calculates the Cartesian coordinate (x, y) of the arm's center
    given the motor angles (theta1, theta2).

    This version correctly models the five-bar parallel SCARA linkage
    by enforcing the geometric constraints derived from the inverse_kinematics function.
    """
    cfg = machine.config['kinematics']
    L1, L3 = cfg['L1'], cfg['L3']

    # Convert angles to radians for math functions
    theta1_rad = math.radians(theta1)
    theta2_rad = math.radians(theta2)

    # 1. Find the position of the primary elbow joint (p1).
    p1_x = L1 * math.cos(theta1_rad)
    p1_y = L1 * math.sin(theta1_rad)
    
    # 2. The core constraint of this linkage is that the vector from p1 to p4
    #    is parallel to the vector from the origin to p2, but points in the
    #    opposite direction. Therefore, its angle is theta2 + 180 degrees.
    #    cos(t + 180) = -cos(t)
    #    sin(t + 180) = -sin(t)
    #    So, the vector (p1->p4) can be calculated directly.
    vec_p1_p4_x = -L3 * math.cos(theta2_rad)
    vec_p1_p4_y = -L3 * math.sin(theta2_rad)

    # 3. The final position (p4) is the position of p1 plus the vector from p1 to p4.
    p4_x = p1_x + vec_p1_p4_x
    p4_y = p1_y + vec_p1_p4_y
    
    return (p4_x, p4_y)