#!/usr/bin/env python3
"""
calibrate_fivebar.py

Reads diagnostic motor-step data (saved as JSON by diagnose_motor_steps.py)
and performs a nonlinear least-squares fit to estimate the actual geometry
of a 2-DOF five-bar parallel robot (link lengths, base separation, offsets).

Usage:
    python calibrate_fivebar.py path/to/sidekick_calibration_<timestamp>.json
"""

import json
import sys
import numpy as np
from math import cos, sin, pi
from pathlib import Path
from scipy.optimize import least_squares
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def load_data(json_path):
    """Load calibration data JSON."""
    with open(json_path, "r", encoding="utf-8") as f:
        blob = json.load(f)

    wells = []
    m1, m2 = [], []
    for d in blob["data"]:
        wells.append(d["well"])
        m1.append(d["final_m1"])
        m2.append(d["final_m2"])

    return {
        "timestamp": blob.get("timestamp", ""),
        "nominal": blob.get("arm_lengths_nominal_cm", {}),
        "wells": wells,
        "m1": np.array(m1, dtype=float),
        "m2": np.array(m2, dtype=float),
    }


def well_to_xy_cm(well, pitch_mm=9.0):
    """Convert a well label like 'A1' → (x,y) in cm.
       A1 = (0,0), columns → +X, rows → +Y
    """
    row = ord(well[0].upper()) - 65
    col = int(well[1:]) - 1
    mm_to_cm = 0.1
    return (col * pitch_mm * mm_to_cm, row * pitch_mm * mm_to_cm)


def fk(theta1, theta2, L1, L2, L3, Ln):
    """Forward kinematics with coaxial motors (base at origin)."""
    x0, y0 = 0.0, 0.0
    # Elbow points from same origin
    Ax = x0 + L1 * cos(theta1)
    Ay = y0 + L1 * sin(theta1)
    Bx = x0 + L3 * cos(pi - theta2)   # keep same sign convention as before
    By = y0 + L3 * sin(pi - theta2)

    D = np.hypot(Bx - Ax, By - Ay)
    D = max(D, 1e-8)
    a = (L2**2 - Ln**2 + D**2) / (2 * D)
    a = np.clip(a, -max(L2, Ln), max(L2, Ln))
    h_sq = L2**2 - a**2
    if h_sq < 0:
        # if no real intersection, return midpoint between circle centers projected
        xm = Ax + a * (Bx - Ax) / D
        ym = Ay + a * (By - Ay) / D
        return xm, ym
    h = np.sqrt(h_sq)
    xm = Ax + a * (Bx - Ax) / D
    ym = Ay + a * (By - Ay) / D
    xE = xm + h * (By - Ay) / D
    yE = ym - h * (Bx - Ax) / D
    return xE, yE


# ------------------------------------------------------------
# Main calibration fitting
# ------------------------------------------------------------

def main(json_path):
    data = load_data(json_path)

    wells = data["wells"]
    xy_targets = np.array([well_to_xy_cm(w) for w in wells])
    m1_steps = data["m1"]
    m2_steps = data["m2"]

    # --- Robot constants ---
    nominal = data["nominal"]
    L1_0 = nominal.get("L1", 7.0)
    L2_0 = nominal.get("L2", 3.0)
    L3_0 = nominal.get("L3", 10.0)
    Ln_0 = nominal.get("Ln", 0.5)
    d0 = 10.0  # reasonable default base separation (cm)

    # --- Step conversion ---
    STEPS_PER_REV = 3200  # modify if your hardware differs
    STEP_TO_RAD = 2 * np.pi / STEPS_PER_REV

    def residuals(params):
        # params: [L1, L2, L3, Ln, off1, off2, k]
        L1, L2, L3, Ln, off1, off2, k = params
        pts = []
        for s1, s2 in zip(m1_steps, m2_steps):
            t1 = (s1 - off1) * STEP_TO_RAD * k
            t2 = (s2 - off2) * STEP_TO_RAD * k
            try:
                x, y = fk(t1, t2, L1, L2, L3, Ln)
            except Exception:
                x, y = np.nan, np.nan
            pts.append((x, y))
        pts = np.array(pts)
        if not np.isfinite(pts).all():
            pts = np.nan_to_num(pts, nan=1e3, posinf=1e3, neginf=-1e3)
        return (pts - xy_targets).ravel()

    # Initial guesses
    p0 = [L1_0, L2_0, L3_0, Ln_0, 0.0, 0.0, 1.0]
    bounds = (
        [L1_0*0.6, L2_0*0.6, L3_0*0.6, Ln_0*0.4, -1e5, -1e5, 0.85],
        [L1_0*1.4, L2_0*1.4, L3_0*1.4, Ln_0*2.0,  1e5,  1e5, 1.15]
    )

    # --- Fit ---
    res = least_squares(residuals, p0, bounds=bounds)
    L1, L2, L3, Ln, off1, off2, k = res.x

    print("\n=== Five-Bar Calibration Results ===")
    print(f"Fitted using {len(wells)} wells")
    print("-----------------------------------")
    for name, val in zip(["L1","L2","L3","Ln","offset1","offset2","scale_k"], res.x):
        print(f"{name:>8s}: {val:9.5f}")
    rms = np.sqrt(np.mean(res.fun**2))
    print("-----------------------------------")
    print(f"RMS positional error: {rms*10:.3f} mm")  # convert cm→mm

    # --- Optional plot ---
    try:
        pts_model = []
        for s1, s2 in zip(m1_steps, m2_steps):
            t1 = (s1 - off1) * STEP_TO_RAD * k
            t2 = (s2 - off2) * STEP_TO_RAD * k
            x, y = fk(t1, t2, L1, L2, L3, Ln, d)
            pts_model.append((x, y))
        pts_model = np.array(pts_model)

        plt.figure(figsize=(6,6))
        plt.scatter(xy_targets[:,0], xy_targets[:,1], label="Target Wells", c="blue")
        plt.scatter(pts_model[:,0], pts_model[:,1], label="Model Fit", c="orange", marker="x")
        for (tx,ty),(mx,my),label in zip(xy_targets, pts_model, wells):
            plt.plot([tx,mx],[ty,my],"--",color="gray",alpha=0.5)
            plt.text(tx,ty,label,fontsize=8)
        plt.axis("equal")
        plt.xlabel("X (cm)")
        plt.ylabel("Y (cm)")
        plt.title("Five-Bar Calibration Fit")
        plt.legend()
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"(Plot skipped: {e})")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python calibrate_fivebar.py <calibration_json>")
        sys.exit(1)
    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Error: file not found: {json_path}")
        sys.exit(1)
    main(json_path)
