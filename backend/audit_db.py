import sqlite3
import json

DB_PATH = "lumierecraft.db"

def audit():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, composition, lighting, camera_angle, lens, camera_movement FROM shotblueprint")
    rows = cursor.fetchall()
    
    print(f"Total shotblueprint records: {len(rows)}")
    
    legacy_count = 0
    null_count = 0
    structured_count = 0

    for row in rows:
        d = dict(row)
        is_legacy = False
        is_null = True
        for field in ['composition', 'lighting', 'camera_angle', 'lens', 'camera_movement']:
            val = d[field]
            if val is not None:
                is_null = False
                # Try to parse as JSON
                try:
                    parsed = json.loads(val)
                    if not isinstance(parsed, dict):
                        is_legacy = True
                except:
                    is_legacy = True
        if is_null:
            null_count += 1
        elif is_legacy:
            legacy_count += 1
        else:
            structured_count += 1

        if is_legacy and legacy_count == 1:
            print("\nExample of legacy data:")
            for field in ['composition', 'lighting', 'camera_angle', 'lens', 'camera_movement']:
                print(f"  {field}: {d[field]}")

    print("\nAudit Summary:")
    print(f"Null records: {null_count}")
    print(f"Structured records (valid JSON): {structured_count}")
    print(f"Legacy records (plain strings): {legacy_count}")

    conn.close()

if __name__ == "__main__":
    audit()
