# backend/init_definitivo.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db


def init_definitivo():
    """Inicialização definitiva do banco"""
    print("=" * 60)
    print("INICIALIZAÇÃO DEFINITIVA DO BANCO DE DADOS")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # 1. Criar todas as tabelas
        print("1. Criando todas as tabelas...")
        db.create_all()
        print("✓ Todas as tabelas criadas")

        # 2. Mostrar tabelas criadas
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()

        print(f"\n2. Tabelas no banco ({len(tabelas)}):")
        for tabela in sorted(tabelas):
            print(f"   - {tabela}")

        print("\n" + "=" * 60)
        print("✅ BANCO DE DADOS PRONTO!")
        print("=" * 60)
        print("\nAgora execute: python seed_simples_final.py")
        print("=" * 60)


if __name__ == "__main__":
    init_definitivo()
