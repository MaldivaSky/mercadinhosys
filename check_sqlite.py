import sqlite3
import os

db_path = r'c:\Users\rafae\OneDrive\Desktop\mercadinhosys\backend\instance\mercadinho.db'
if not os.path.exists(db_path):
    print(f"File not found: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables found: {tables}")
    conn.close()
