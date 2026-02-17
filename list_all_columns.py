
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
        print("TABLES AND COLUMNS:")
        res = conn.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' ORDER BY table_name, column_name"))
        for row in res:
            print(f"{row[0]}.{row[1]}")

if __name__ == "__main__":
    check_schema()
