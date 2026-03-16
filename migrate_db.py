import sqlite3
import os

db_path = 'instance/database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_to_add = [
        ("target_calories", "REAL DEFAULT 2500.0"),
        ("target_protein", "REAL DEFAULT 150.0"),
        ("target_carbs", "REAL DEFAULT 300.0"),
        ("target_fat", "REAL DEFAULT 80.0"),
        ("target_fiber", "REAL DEFAULT 30.0")
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
