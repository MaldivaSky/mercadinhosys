
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
    "vendas", "despesas", "contas_pagar", 
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
        print(f"Error querying estabelecimentos: {e}")

    # 2. Check Counts per Table
    print("\n--- Counts per Table ---")
    for tbl in tables:
        try:
            # We use a separate sub-transaction or just fresh execution to avoid aborting the whole thing
            total = conn.execute(text(f"SELECT count(*) FROM {tbl}")).scalar()
            try:
                est1 = conn.execute(text(f"SELECT count(*) FROM {tbl} WHERE estabelecimento_id = 1")).scalar()
            except:
                est1 = "N/A"
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
    
    # 4. Check for current month's data
    print("\n--- Current Month Data (March 2026) ---")
    try:
        # Check sales in March
        sales_mar = conn.execute(text("SELECT count(*) FROM vendas WHERE data_venda >= '2026-03-01'")).scalar()
        # Check expenses in March
        exp_mar = conn.execute(text("SELECT count(*) FROM despesas WHERE data_despesa >= '2026-03-01'")).scalar()
        print(f"Sales in March: {sales_mar}")
        print(f"Expenses in March: {exp_mar}")
    except Exception as e:
        print(f"Error: {e}")
