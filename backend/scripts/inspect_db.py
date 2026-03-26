import sqlite3
import os

db_path = "instance/mercadinho_local.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(auditoria)")
    cols = cursor.fetchall()
    print("Table: auditoria")
    for col in cols:
        print(col)
    conn.close()
else:
    print(f"File not found: {db_path}")
