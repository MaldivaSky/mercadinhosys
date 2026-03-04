
import os
import sys
sys.path.append(os.getcwd() + "/backend")

from app import create_app, db
from app.models import Despesa, Venda, ContaPagar, MovimentacaoCaixa, Estabelecimento
from datetime import datetime, timedelta

def audit_db(uri):
    print(f"\n=== Auditing DB: {uri} ===")
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    with app.app_context():
        est = Estabelecimento.query.first()
        if not est:
            print("No establishment found in this DB.")
            return
        
        est_id = est.id
        print(f"Establishment ID: {est_id} ({est.nome_fantasia})")
        
        print(f"Despesas: {Despesa.query.filter_by(estabelecimento_id=est_id).count()}")
        print(f"Vendas (finalizadas): {Venda.query.filter_by(estabelecimento_id=est_id, status='finalizada').count()}")
        print(f"ContasPagar: {ContaPagar.query.filter_by(estabelecimento_id=est_id).count()}")
        print(f"Movimentacoes: {MovimentacaoCaixa.query.filter_by(estabelecimento_id=est_id).count()}")

# Audit Postgres
pg_uri = "postgresql://mercadinho_user:mercadinho_secure_pass_2024@localhost:5432/mercadinhosys"
audit_db(pg_uri)

# Audit SQLite
sqlite_path = os.getcwd() + "/backend/mercadinhosys_dev.sqlite"
if os.path.exists(sqlite_path):
    sqlite_uri = f"sqlite:///{sqlite_path}"
    audit_db(sqlite_uri)
else:
    print(f"\nSQLite DB not found at {sqlite_path}")
