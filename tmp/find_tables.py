
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.getenv("DATABASE_URL")
AIVEN_URL = os.getenv("AIVEN_DATABASE_URL")

def check_db(url, label):
    if not url:
        return
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    print(f"\n--- Checking {label} ---")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'")).fetchall()
            if not result:
                print("No tables found.")
            else:
                print("Tables found:")
                for row in result:
                    print(f"  - {row[0]}")
    except Exception as e:
        print(f"Error: {e}")

check_db(DATABASE_URL, "Local Postgres")
check_db(AIVEN_URL, "Aiven Cloud")

print("\n--- Checking SQLite Files ---")
from pathlib import Path
for p in Path(".").rglob("*.db"):
    print(f"File: {p}")
    try:
        engine = create_engine(f"sqlite:///{p.absolute()}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            print("  Tables:", [r[0] for r in result])
    except Exception as e:
        print(f"  Error: {e}")
