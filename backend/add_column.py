import sqlite3

conn = sqlite3.connect('c:/temp/mercadinho_instance/mercadinho.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE funcionarios ADD COLUMN status VARCHAR(20) DEFAULT 'ativo'")
    conn.commit()
    print("Column added successfully")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

conn.close()