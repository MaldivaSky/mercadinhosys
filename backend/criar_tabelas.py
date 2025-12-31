# backend/criar_todas_tabelas.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import *  # Importa todos os modelos para garantir que sejam registrados

app = create_app()

with app.app_context():
    print("Criando todas as tabelas...")
    db.create_all()  # Isso criará todas as tabelas definidas nos modelos
    print("Tabelas criadas com sucesso!")

    # Verificar tabelas criadas
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    tabelas = inspector.get_table_names()
    print("\nTabelas no banco de dados:")
    for tabela in sorted(tabelas):
        print(f"  - {tabela}")
