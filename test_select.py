import os
import psycopg2

def test_select():
    uri = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    if not uri:
        print("Defina AIVEN_DATABASE_URL ou DATABASE_URL")
        return
    
    try:
        conn = psycopg2.connect(uri)
        cur = conn.cursor()
        
        print("Tentando SELECT preco_custo FROM produtos LIMIT 1...")
        cur.execute("SELECT preco_custo FROM produtos LIMIT 1;")
        res = cur.fetchone()
        print(f"Resultado: {res}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERRO NO SELECT DIRETO: {e}")

if __name__ == "__main__":
    test_select()
