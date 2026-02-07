#!/usr/bin/env python3
"""
Script para limpar completamente o banco Neon
Identifica todas as tabelas dinamicamente
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()

target_url = os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL')
if not target_url:
    print("[ERRO] NEON_DATABASE_URL nao configurado")
    exit(1)

if target_url.startswith("postgres://"):
    target_url = target_url.replace("postgres://", "postgresql://", 1)

print(f"[CONECTANDO] Neon...")

try:
    engine = create_engine(target_url)
    
    # Inspecionar banco para encontrar todas as tabelas
    inspector = inspect(engine)
    tabelas = inspector.get_table_names()
    
    print(f"[ENCONTRADO] {len(tabelas)} tabelas")
    for t in tabelas:
        print(f"  - {t}")
    
    # Conectar e limpar
    with engine.connect() as conn:
        # DELETE FROM cada tabela em ordem reversa (sem SET commands)
        for tabela in reversed(tabelas):
            try:
                conn.execute(text(f"DELETE FROM {tabela}"))
                conn.commit()
                print(f"  [OK] {tabela}")
            except Exception as e:
                print(f"  [AVISO] {tabela}: {str(e)[:60]}")
                conn.rollback()
                continue
    
    print("[OK] Banco Neon limpo com sucesso")

except Exception as e:
    print(f"[ERRO] {e}")
    import traceback
    traceback.print_exc()
    exit(1)
