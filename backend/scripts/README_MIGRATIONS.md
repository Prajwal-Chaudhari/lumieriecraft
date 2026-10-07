# Database Migration Guide

This project uses `SQLModel` with a local SQLite database (`lumierecraft.db`). To avoid the overhead of heavy migration frameworks like Alembic for local SQLite development, we provide a simple, repeatable migration utility.

## How it works
The utility inspects your current `lumierecraft.db` and compares it against the declared `SQLModel` schemas in `app/models/`. 
- **Missing Columns:** If you add new fields to your models, the script detects them and generates `ALTER TABLE ADD COLUMN` statements. 
- **Removed Columns:** If you remove fields, it generates `ALTER TABLE DROP COLUMN` statements.

## Steps to Migrate

1. **Backup Your Database (Highly Recommended):**
   ```bash
   copy lumierecraft.db lumierecraft_backup.db
   ```

2. **Check for Schema Changes (Dry Run):**
   Run the migration script to see what changes will be applied. It will print out the missing and extra columns without modifying the database.
   ```bash
   set PYTHONPATH=.
   venv\Scripts\python scripts\db_migrate.py
   ```

3. **Apply the Migration:**
   Once you're satisfied with the proposed changes, apply them:
   ```bash
   set PYTHONPATH=.
   venv\Scripts\python scripts\db_migrate.py --apply
   ```

## Notes and Limitations
- **SQLite 3.35.0+ Required:** Dropping columns requires modern SQLite. Python 3.10+ generally bundles compatible SQLite versions.
- **Indexes on Dropped Columns:** If you attempt to drop a column that has an index, SQLite may throw an error. You must manually drop the index first via the `sqlite3` CLI or a custom script before applying the migration.
- **JSON Defaults:** The migration script attempts to assign `DEFAULT '[]'` for list-like JSON fields (ending in 's' or 'list') and `DEFAULT '{}'` for other JSON objects. If you need a specific default, consider writing a custom `ALTER TABLE` statement.
- **New Tables:** This script does not create new tables. When you add a new model, you should rely on `SQLModel.metadata.create_all(engine)` which is executed on application startup to create any missing tables.
