# backend/verificar_db.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("Verificando estado do banco de dados...")

    inspector = inspect(db.engine)
    tabelas = inspector.get_table_names()

    print(f"\nTabelas encontradas ({len(tabelas)}):")
    for tabela in sorted(tabelas):
        print(f"  - {tabela}")

    # Tabelas esperadas do models.py
    tabelas_esperadas = [
        "estabelecimentos",
        "configuracoes",
        "funcionarios",
        "clientes",
        "fornecedores",
        "produtos",
        "vendas",
        "venda_itens",
        "movimentacoes_estoque",
        "dashboard_metricas",
        "relatorios_agendados",
    ]

    print(f"\nTabelas faltantes:")
    faltantes = [t for t in tabelas_esperadas if t not in tabelas]
    if faltantes:
        for t in faltantes:
            print(f"  - {t}")

        resposta = input("\nDeseja criar as tabelas faltantes? (s/n): ").lower()
        if resposta == "s":
            print("Criando tabelas...")
            from app.models import *

            db.create_all()
            print("Tabelas criadas com sucesso!")
    else:
        print("✓ Todas as tabelas necessárias existem!")

    # Contar registros
    print("\nContagem de registros:")
    for tabela in sorted(tabelas_esperadas):
        if tabela in tabelas:
            try:
                if tabela == "alembic_version":
                    continue
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
                count = result.scalar()
                print(f"  - {tabela}: {count} registros")
            except Exception as e:
                print(f"  - {tabela}: erro ao contar - {e}")
