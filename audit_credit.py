
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv

# Path setup to ensure 'app' can be imported
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

load_dotenv(dotenv_path="backend/.env")

from backend.app import create_app
from backend.app.models import db, Estabelecimento, Venda, Cliente, MovimentacaoCaixa

def audit_credit_data():
    app = create_app()
    with app.app_context():
        print(f"DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Check Establishments
        ests = Estabelecimento.query.all()
        if not ests:
            print("❌ No establishments found!")
            return

        for est in ests:
            print(f"\n--- Establishment: {est.nome_fantasia} (ID: {est.id}) ---")
            
            # 1. Check Clients with Debt
            clients_with_debt = Cliente.query.filter_by(estabelecimento_id=est.id).filter(Cliente.saldo_devedor > 0).count()
            total_debt = db.session.query(db.func.sum(Cliente.saldo_devedor)).filter_by(estabelecimento_id=est.id).scalar() or 0
            print(f"Clients with debt: {clients_with_debt}")
            print(f"Total current debt (saldo_devedor): R$ {total_debt:,.2f}")
            
            # 2. Check Fiado Sales
            fiado_sales = Venda.query.filter_by(estabelecimento_id=est.id).filter(Venda.forma_pagamento.ilike('%fiado%')).count()
            fiado_volume = db.session.query(db.func.sum(Venda.total)).filter_by(estabelecimento_id=est.id).filter(Venda.forma_pagamento.ilike('%fiado%')).scalar() or 0
            print(f"Sales with payment 'fiado': {fiado_sales}")
            print(f"Volume of 'fiado' sales: R$ {fiado_volume:,.2f}")
            
            # 3. Check Payments (MovimentacaoCaixa)
            # Looking for receipts that might be payments of debt
            payments = MovimentacaoCaixa.query.filter_by(estabelecimento_id=est.id).filter(
                db.or_(
                    MovimentacaoCaixa.descricao.ilike('%Fiado%'),
                    MovimentacaoCaixa.observacoes.ilike('%Fiado%'),
                    MovimentacaoCaixa.descricao.ilike('%Recebimento%')
                )
            ).count()
            payment_vol = db.session.query(db.func.sum(MovimentacaoCaixa.valor)).filter_by(estabelecimento_id=est.id).filter(
                db.or_(
                    MovimentacaoCaixa.descricao.ilike('%Fiado%'),
                    MovimentacaoCaixa.observacoes.ilike('%Fiado%'),
                    MovimentacaoCaixa.descricao.ilike('%Recebimento%')
                )
            ).scalar() or 0
            print(f"Potential debt payment entries: {payments}")
            print(f"Volume of potential payments: R$ {payment_vol:,.2f}")

if __name__ == "__main__":
    audit_credit_data()
