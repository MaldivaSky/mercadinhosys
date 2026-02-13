
from app import create_app
from app.models import db, Produto
from datetime import date, timedelta
import json

app = create_app()
with app.app_context():
    # Use est_id 1 as default for dev
    est_id = 1
    
    # Check total produtos
    total = Produto.query.filter_by(estabelecimento_id=est_id, ativo=True).count()
    
    # Check produtos with validity
    with_val = Produto.query.filter(
        Produto.estabelecimento_id == est_id,
        Produto.ativo == True,
        Produto.data_validade.isnot(None)
    ).count()
    
    # Check expired
    hoje = date.today()
    expired = Produto.query.filter(
        Produto.estabelecimento_id == est_id,
        Produto.ativo == True,
        Produto.data_validade < hoje
    ).count()
    
    # Check 15 days
    v15 = Produto.query.filter(
        Produto.estabelecimento_id == est_id,
        Produto.ativo == True,
        Produto.data_validade >= hoje,
        Produto.data_validade <= hoje + timedelta(days=15)
    ).count()

    print(f"Total Produtos (Est 1): {total}")
    print(f"Produtos com Validade: {with_val}")
    print(f"Vencidos: {expired}")
    print(f"Vence em 15 dias: {v15}")

    # Check some actual values
    sample = Produto.query.filter(Produto.data_validade.isnot(None)).limit(5).all()
    for s in sample:
        print(f"ID: {s.id}, Nome: {s.nome}, Validade: {s.data_validade}, Ativo: {s.ativo}")
