
from app import create_app
from app.models import db, Produto
from datetime import date, timedelta

app = create_app()
with app.app_context():
    est_id = 1
    total = Produto.query.filter_by(estabelecimento_id=est_id, ativo=True).count()
    with_val = Produto.query.filter(Produto.estabelecimento_id==est_id, Produto.ativo==True, Produto.data_validade.isnot(None)).count()
    hoje = date.today()
    
    expired = Produto.query.filter(Produto.estabelecimento_id==est_id, Produto.ativo==True, Produto.data_validade < hoje).count()
    v15 = Produto.query.filter(Produto.estabelecimento_id==est_id, Produto.ativo==True, Produto.data_validade >= hoje, Produto.data_validade <= hoje + timedelta(days=15)).count()
    v30 = Produto.query.filter(Produto.estabelecimento_id==est_id, Produto.ativo==True, Produto.data_validade >= hoje, Produto.data_validade <= hoje + timedelta(days=30)).count()
    v90 = Produto.query.filter(Produto.estabelecimento_id==est_id, Produto.ativo==True, Produto.data_validade >= hoje, Produto.data_validade <= hoje + timedelta(days=90)).count()

    print(f"--- RESULTS ---")
    print(f"Total: {total}")
    print(f"WithVal: {with_val}")
    print(f"Expired: {expired}")
    print(f"V15: {v15}")
    print(f"V30: {v30}")
    print(f"V90: {v90}")
    print(f"--- END ---")
