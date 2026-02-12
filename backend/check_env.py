from app import db, create_app
from app.models import Funcionario, Estabelecimento, Produto
import os

app = create_app()
with app.app_context():
    print("--- ESTABELECIMENTOS ---")
    ests = Estabelecimento.query.all()
    for e in ests:
        print(f"ID: {e.id}, Nome: {e.nome_fantasia}")
        
    print("\n--- FUNCIONARIOS ---")
    funcs = Funcionario.query.all()
    for f in funcs:
        print(f"ID: {f.id}, Nome: {f.nome}, Est ID: {f.estabelecimento_id}")
        
    print("\n--- PRODUTOS DISTRIBUICAO ---")
    dist = db.session.query(Produto.estabelecimento_id, db.func.count(Produto.id)).group_by(Produto.estabelecimento_id).all()
    print(dist)
