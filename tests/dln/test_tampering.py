# test_tampering.py
# This test assumes that the database contains finialized sessions with ids 63 and 64.
# It will alter session 64.
import sqlite3
import os
from dln.verification import check_integrity

# Path to your database
DB_PATH = ".talos/lab_notebook.db"

def run_test():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at '{DB_PATH}'")
        return

    print("=== Step 1: Initial Integrity Check ===")
    try:
        is_63_valid = check_integrity(DB_PATH, 63)
        print(f"Session 63 (Untouched) is valid: {is_63_valid}")
    except Exception as e:
        print(f"Session 63 check failed: {e}")

    try:
        is_64_valid = check_integrity(DB_PATH, 64)
        print(f"Session 64 (Pre-tampering) is valid: {is_64_valid}")
    except Exception as e:
        print(f"Session 64 check failed: {e}")


    print("\n=== Step 2: Simulating Tampering on Session 64 ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find the first ScienceLog entry associated with Session 64
    cursor.execute("SELECT id, data FROM ScienceLog WHERE session_id = 64 LIMIT 1;")
    row = cursor.fetchone()

    if row:
        log_id, original_data = row
        print(f"Found ScienceLog Entry ID: {log_id}")
        print(f"Original Data: {original_data}")

        # Modify the data slightly (e.g., change a parameter or note)
        tampered_data = '{"message": "This record has been maliciously modified."}'
        
        cursor.execute("UPDATE ScienceLog SET data = ? WHERE id = ?;", (tampered_data, log_id))
        conn.commit()
        print(f"Successfully altered ScienceLog Entry ID: {log_id}")
    else:
        print("Warning: No ScienceLog records found for Session 64 to alter.")
    
    conn.close()


    print("\n=== Step 3: Post-Tampering Integrity Check ===")
    try:
        is_63_valid_post = check_integrity(DB_PATH, 63)
        print(f"Session 63 (Untouched) remains valid: {is_63_valid_post}")
    except Exception as e:
        print(f"Session 63 check failed: {e}")

    try:
        is_64_valid_post = check_integrity(DB_PATH, 64)
        print(f"Session 64 (Tampered) is valid: {is_64_valid_post}")
    except Exception as e:
        print(f"Session 64 check failed: {e}")

if __name__ == "__main__":
    run_test()