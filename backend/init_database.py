# backend/init_database.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db


def init_database():
    """Inicializa o banco de dados corretamente"""
    print("Inicializando banco de dados...")

    app = create_app()

    with app.app_context():
        # Primeiro, tente usar Flask-Migrate
        try:
            print("Tentando usar Flask-Migrate...")
            from flask_migrate import upgrade

            upgrade()
            print("✓ Migrações aplicadas com Flask-Migrate")
        except Exception as e:
            print(f"Flask-Migrate não disponível: {e}")
            print("Criando tabelas manualmente...")

            # Criar todas as tabelas
            db.create_all()
            print("✓ Tabelas criadas manualmente")

        # Verificar tabelas criadas
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()

        print(f"\nTabelas criadas ({len(tabelas)}):")
        for tabela in sorted(tabelas):
            print(f"  - {tabela}")


if __name__ == "__main__":
    init_database()
