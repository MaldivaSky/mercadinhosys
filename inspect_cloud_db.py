
import os
import sys
from sqlalchemy import create_engine, text

def check_schema():
    uri = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    if not uri:
        print("Defina AIVEN_DATABASE_URL ou DATABASE_URL")
        return
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    print(f"Connecting to: {uri[:40]}...")
    engine = create_engine(uri)
    
    tables = ["estabelecimentos", "produtos", "venda_itens", "vendas", "historico_precos"]
    
    with engine.connect() as conn:
        for table in tables:
            print(f"\n--- Columns in {table} ---")
            try:
                res = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"))
                cols = res.fetchall()
                if not cols:
                    print("  [!] Table NOT FOUND or empty information_schema")
                for col in cols:
                    print(f"  - {col[0]} ({col[1]})")
            except Exception as e:
                print(f"  [!] Error checking {table}: {e}")

        print("\n--- Rows Count ---")
        for table in tables:
            try:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = res.scalar()
                print(f"  {table}: {count} rows")
            except Exception as e:
                print(f"  {table}: ERROR count")

if __name__ == "__main__":
    check_schema()
