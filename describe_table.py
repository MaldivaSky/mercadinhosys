import os
import psycopg2

def describe_table():
    uri = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    if not uri:
        print("Defina AIVEN_DATABASE_URL ou DATABASE_URL")
        return
    
    try:
        conn = psycopg2.connect(uri)
        cur = conn.cursor()
        
        print("--- DESCRIÇÃO DA TABELA PRODUTOS ---")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'produtos'
            ORDER BY ordinal_position;
        """)
        
        rows = cur.fetchall()
        for row in rows:
            print(f"Col: {row[0]}, Type: {row[1]}, Null: {row[2]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    describe_table()
