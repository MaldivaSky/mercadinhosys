import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app, db
from app.models import Venda, Estabelecimento, Funcionario

app = create_app()

with app.app_context():
    print("--- Database Audit ---")
    
    total_vendas = Venda.query.count()
    print(f"Total sales in DB: {total_vendas}")
    
    estabelecimentos = Estabelecimento.query.all()
    print(f"Total establishments: {len(estabelecimentos)}")
    
    for est in estabelecimentos:
        vendas_est = Venda.query.filter_by(estabelecimento_id=est.id).count()
        print(f"Est ID {est.id} ({est.nome_fantasia}): {vendas_est} sales")
        
    print("\n--- Recent Sales ---")
    recent_sales = Venda.query.order_by(Venda.created_at.desc()).limit(5).all()
    for s in recent_sales:
        print(f"Sale {s.id}: Est {s.estabelecimento_id}, Total {s.total}, Date {s.data_venda or s.created_at}")

    print("\n--- Current Users ---")
    users = Funcionario.query.limit(10).all()
    for u in users:
        print(f"User {u.username}: Est {u.estabelecimento_id}, Role {u.role}")
