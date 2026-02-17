
import os
from sqlalchemy import create_engine, text

def check_schema():
    uri = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    if not uri:
        print("Defina AIVEN_DATABASE_URL ou DATABASE_URL")
        return
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(uri)
    
    with engine.connect() as conn:
        print("TABLE_COLUMNS_START")
        res = conn.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'produtos' ORDER BY column_name"))
        for row in res:
            print(f"PRODUTO_COL: {row[1]}")
        print("TABLE_COLUMNS_END")

if __name__ == "__main__":
    check_schema()
