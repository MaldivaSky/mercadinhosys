
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

tables = [
    "estabelecimentos", "vendas", "despesas", "contas_pagar", 
    "clientes", "movimentacoes_caixa", "fornecedores", "produtos"
]

with engine.connect() as conn:
    print(f"Connected to: {DATABASE_URL.split('@')[-1]}")
    
    # 1. Check Establishments
    print("\n--- Establishments ---")
    try:
        ests = conn.execute(text("SELECT id, nome_fantasia FROM estabelecimentos")).fetchall()
        for row in ests:
            print(f"ID: {row[0]}, Nome: {row[1]}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Check Counts per Establishment
    print("\n--- Counts per Table ---")
    for tbl in tables:
        try:
            total = conn.execute(text(f"SELECT count(*) FROM {tbl}")).scalar()
            est1 = conn.execute(text(f"SELECT count(*) FROM {tbl} WHERE estabelecimento_id = 1")).scalar()
            print(f"{tbl:<20}: Total={total}, Est 1={est1}")
        except Exception as e:
            print(f"Error querying {tbl}: {e}")

    # 3. Check for 'fiado' specifically
    print("\n--- Fiado Specifics ---")
    try:
        fiado_count = conn.execute(text("SELECT count(*) FROM vendas WHERE forma_pagamento ILIKE '%fiado%'")).scalar()
        print(f"Total Fiado Sales: {fiado_count}")
    except Exception as e:
        print(f"Error: {e}")
