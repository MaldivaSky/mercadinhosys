from app import db, create_app
from app.models import Produto
from datetime import date

app = create_app()
with app.app_context():
    total = db.session.query(Produto).count()
    ativos = db.session.query(Produto).filter(Produto.ativo == True).count()
    com_validade = db.session.query(Produto).filter(Produto.data_validade.isnot(None)).count()
    ativos_com_validade = db.session.query(Produto).filter(Produto.ativo == True, Produto.data_validade.isnot(None)).count()
    
    print(f"Total: {total}")
    print(f"Ativos: {ativos}")
    print(f"Com validade: {com_validade}")
    print(f"Ativos com validade: {ativos_com_validade}")
    
    abc_dist = db.session.query(Produto.classificacao_abc, db.func.count(Produto.id)).group_by(Produto.classificacao_abc).all()
    print(f"Distribuição ABC: {abc_dist}")
    
    amostra = db.session.query(Produto.nome, Produto.data_validade, Produto.controlar_validade).filter(Produto.data_validade.isnot(None)).limit(5).all()
    for p in amostra:
        print(f"- {p.nome}: {p.data_validade} (controlar: {p.controlar_validade})")
