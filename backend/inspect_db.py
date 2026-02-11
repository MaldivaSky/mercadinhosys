import sqlite3
import os

db_path = 'instance/mercadinho.db'
if not os.path.exists(db_path):
    print(f"File {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- TABLES ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        print(f"Table: {row[0]}")
        
    print("\n--- TRIGGER ---")
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
    for row in cursor.fetchall():
        print(f"Trigger: {row[0]}\nSQL: {row[1]}\n")
        
    print("\n--- PRAGMA table_info(produtos) ---")
    cursor.execute("PRAGMA table_info(produtos)")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()
