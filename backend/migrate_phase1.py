import sqlite3
import os

DB_PATH = "lumierecraft.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create CharacterAsset table
    print("Creating characterasset table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characterasset (
            id TEXT NOT NULL PRIMARY KEY,
            project_id TEXT NOT NULL,
            character_id TEXT,
            character_name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            source TEXT NOT NULL,
            description TEXT,
            continuity_notes TEXT,
            created_at DATETIME NOT NULL,
            FOREIGN KEY(project_id) REFERENCES project (id)
        )
    ''')

    # Add new JSON columns to shotblueprint
    # In SQLite, ALTER TABLE ADD COLUMN can only add one column at a time
    print("Checking shotblueprint for new columns...")
    cursor.execute("PRAGMA table_info(shotblueprint)")
    columns = [row[1] for row in cursor.fetchall()]

    new_columns = ["camera", "blocking", "color"]
    for col in new_columns:
        if col not in columns:
            print(f"Adding column {col} to shotblueprint...")
            cursor.execute(f"ALTER TABLE shotblueprint ADD COLUMN {col} JSON")

    # The existing columns 'composition' and 'lighting' are strings (VARCHAR). 
    # We can leave their types as they are (since sqlite doesn't care) but they will now store JSON strings.
    # However, 'camera_angle', 'lens', 'camera_movement', 'visual_prompt' are no longer in the Pydantic model. 
    # We don't drop them to preserve existing data, they just become orphaned columns.

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
