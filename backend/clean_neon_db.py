#!/usr/bin/env python3
"""
Limpador de banco Neon com DELETE simples (sem SET commands)
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

target_url = os.environ.get('AIVEN_DATABASE_URL') or os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL')
if not target_url:
    print("[ERRO] AIVEN_DATABASE_URL nao configurado")
    exit(1)

if target_url.startswith("postgres://"):
    target_url = target_url.replace("postgres://", "postgresql://", 1)

print(f"[CONECTANDO] {target_url.split('@')[1] if '@' in target_url else target_url}")

try:
    engine = create_engine(target_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Disabilitar todas as constraints
    tabelas = [
        'movimentacoes_estoque',
        'vendas_items',
        'pagamentos',
        'vendas',
        'caixas',
        'registro_ponto',
        'configuracao_horario',
        'produtos',
        'movimentacoes_caixa',
        'dashboard_metricas',
        'categorias_produto',
        'fornecedores',
        'clientes',
        'login_history',
        'funcionarios',
        'configuracao',
        'despesas',
        'estabelecimentos'
    ]
    
    print("[LIMPANDO] Deletando registros em ordem...")
    
    for tabela in tabelas:
        try:
            session.execute(text(f"DELETE FROM {tabela}"))
            session.commit()
            print(f"  [OK] {tabela}")
        except Exception as e:
            print(f"  [SKIP] {tabela}: {str(e)[:60]}")
            session.rollback()
    
    session.close()
    print("[OK] Banco limpo com sucesso")

except Exception as e:
    print(f"[ERRO] {e}")
    exit(1)
