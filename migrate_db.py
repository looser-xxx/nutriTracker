import sqlite3
import os

db_path = 'instance/database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Correct columns as per current User model in models.py
    columns_to_add = [
        ("weight", "REAL"),
        ("bicepSize", "REAL"),
        ("age", "INTEGER"),
        ("targetWater", "REAL DEFAULT 3000.0")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Migration completed.")
else:
    print("Database file not found.")
