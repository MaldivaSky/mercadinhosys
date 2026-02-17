
import psycopg2
import os
from dotenv import load_dotenv

def list_all_cols_with_schema():
    load_dotenv('backend/.env.render') # Usar config da nuvem
    url = os.getenv('DATABASE_URL')
    if not url:
        print("DATABASE_URL não encontrada em .env.render")
        return

    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        print(f"--- LISTANDO TODAS AS COLUNAS POR SCHEMA ---")
        cur.execute("""
            SELECT table_schema, table_name, column_name 
            FROM information_schema.columns 
            WHERE table_name IN ('produtos', 'produto')
            ORDER BY table_schema, table_name, ordinal_position;
        """)
        
        rows = cur.fetchall()
        for row in rows:
            print(f"Schema: {row[0]}, Table: {row[1]}, Column: {row[2]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    list_all_cols_with_schema()
