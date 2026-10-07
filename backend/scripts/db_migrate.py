import sqlite3
import argparse
import sys
from sqlmodel import SQLModel
# Import all models to ensure they are registered with SQLModel.metadata
from app.models.project import Project
from app.models.script import Script, ScriptProposal
from app.models.production import CharacterBible, WorldBible, SceneBreakdown
import sqlalchemy

DEFAULT_DB_PATH = "lumierecraft.db"

def get_sqlite_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row for row in cursor.fetchall()}

def get_sql_type(column_type):
    if isinstance(column_type, sqlalchemy.types.JSON):
        return "JSON"
    elif isinstance(column_type, sqlalchemy.types.DateTime):
        return "DATETIME"
    elif isinstance(column_type, sqlalchemy.types.Integer):
        return "INTEGER"
    elif isinstance(column_type, sqlalchemy.types.Boolean):
        return "BOOLEAN"
    elif isinstance(column_type, sqlalchemy.types.Float):
        return "FLOAT"
    else:
        return "VARCHAR"

def get_default_for_type(col_type_str):
    if col_type_str == "JSON":
        return "DEFAULT '{}'" # Fallback, user might need '[]'
    elif col_type_str == "DATETIME":
        return "DEFAULT CURRENT_TIMESTAMP"
    elif col_type_str in ["INTEGER", "FLOAT"]:
        return "DEFAULT 0"
    elif col_type_str == "BOOLEAN":
        return "DEFAULT 0"
    return "DEFAULT NULL"

def migrate_database(db_path, apply=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Inspecting database schema at {db_path}...")
    
    missing_columns = []
    extra_columns = []
    
    for table_name, table in SQLModel.metadata.tables.items():
        sqlite_cols = get_sqlite_columns(cursor, table_name)
        if not sqlite_cols:
            print(f"Table '{table_name}' does not exist in the database.")
            continue
            
        model_cols = {c.name: c for c in table.columns}
        
        # Check for missing columns (in Model, not in DB)
        for col_name, col_obj in model_cols.items():
            if col_name not in sqlite_cols:
                col_type_str = get_sql_type(col_obj.type)
                missing_columns.append({
                    "table": table_name,
                    "column": col_name,
                    "type": col_type_str,
                    "default": get_default_for_type(col_type_str)
                })
                
        # Check for extra columns (in DB, not in Model)
        for col_name in sqlite_cols.keys():
            if col_name not in model_cols:
                extra_columns.append({
                    "table": table_name,
                    "column": col_name
                })
                
    if not missing_columns and not extra_columns:
        print("Database schema matches SQLModel definitions perfectly. No migration needed.")
        conn.close()
        return

    if missing_columns:
        print("\n--- MISSING COLUMNS (To Add) ---")
        for mc in missing_columns:
            print(f"ALTER TABLE {mc['table']} ADD COLUMN {mc['column']} {mc['type']} {mc['default']}")
            
    if extra_columns:
        print("\n--- EXTRA COLUMNS (To Drop) ---")
        for ec in extra_columns:
            print(f"ALTER TABLE {ec['table']} DROP COLUMN {ec['column']}")
            
    if not apply:
        print("\nRun with --apply to execute these changes.")
        conn.close()
        return
        
    print("\n--- APPLYING MIGRATION ---")
    
    for mc in missing_columns:
        # Simple heuristic to differentiate list vs dict JSON defaults based on pluralization
        # Can be overridden manually if script is run
        default_val = mc['default']
        if mc['type'] == 'JSON' and (mc['column'].endswith('s') or mc['column'].endswith('list')):
            default_val = "DEFAULT '[]'"
            
        stmt = f"ALTER TABLE {mc['table']} ADD COLUMN {mc['column']} {mc['type']} {default_val}"
        print(f"Executing: {stmt}")
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"Error adding column: {e}")
            
    for ec in extra_columns:
        stmt = f"ALTER TABLE {ec['table']} DROP COLUMN {ec['column']}"
        print(f"Executing: {stmt}")
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"Error dropping column (may be indexed): {e}")
            print(f"  Tip: Drop any related indexes on {ec['column']} first.")
            
    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-migrate SQLite DB against SQLModel schemas.")
    parser.add_argument("--apply", action="store_true", help="Apply the migration")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="Path to SQLite DB")
    args = parser.parse_args()
    
    migrate_database(args.db, args.apply)
