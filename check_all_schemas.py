
import psycopg2
import os

def check_all_schemas():
    uri = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    if not uri:
        print("Defina AIVEN_DATABASE_URL ou DATABASE_URL")
        return
    
    try:
        conn = psycopg2.connect(uri)
        cur = conn.cursor()
        
        print(f"--- BUSCANDO TABELAS 'produto' OU 'produtos' EM TODOS OS SCHEMAS ---")
        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables 
            WHERE table_name IN ('produtos', 'produto')
            ORDER BY table_schema, table_name;
        """)
        
        tables = cur.fetchall()
        for t in tables:
            print(f"Schema: {t[0]}, Table: {t[1]}")
            # Ver cols dessa tabela
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{t[0]}' AND table_name = '{t[1]}';")
            cols = [c[0] for c in cur.fetchall()]
            print(f"  Colunas: {cols}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_all_schemas()
