
import os
import sys

# Adiciona o diretório atual ao sys.path para importar o app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Funcionario, Estabelecimento

app = create_app()

with app.app_context():
    print(f"--- ESTABELECIMENTOS ---")
    estabs = Estabelecimento.query.all()
    for e in estabs:
        print(f"ID: {e.id}, Nome: {e.nome_fantasia}")
        
    print(f"\n--- TODOS OS FUNCIONÁRIOS ---")
    funcs = Funcionario.query.all()
    for f in funcs:
        print(f"ID: {f.id}, Nome: {f.nome}, Estab ID: {f.estabelecimento_id}, Username: {f.username}, Role: {f.role}")
