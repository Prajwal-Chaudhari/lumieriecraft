import sqlite3

def migrate():
    conn = sqlite3.connect('lumierecraft.db')
    cursor = conn.cursor()

    try:
        # Drop old tables
        cursor.execute("DROP TABLE IF EXISTS characterbible")
        cursor.execute("DROP TABLE IF EXISTS worldbible")
        cursor.execute("DROP TABLE IF EXISTS scenebreakdown")
        cursor.execute("DROP TABLE IF EXISTS storyboardframe")
        cursor.execute("DROP TABLE IF EXISTS shotblueprint")
        cursor.execute("DROP TABLE IF EXISTS productionplan")
        cursor.execute("DROP TABLE IF EXISTS cinematographyproposal")
        
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
    from app.db import engine
    from app.models.project import Project
    from app.models.script import Script
    from app.models.production import SQLModel
    SQLModel.metadata.create_all(engine)
    print("Migration completed.")
