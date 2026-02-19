
import sys
import os
import logging
from app import create_app, db
from app.models import Venda
from sqlalchemy import func

# Add backend directory to path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)

def check_dates():
    app = create_app()
    with app.app_context():
        print("--- Verificando Datas das Vendas (ID 1) ---")
        sales = db.session.query(Venda.data_venda).filter(
            Venda.estabelecimento_id == 1,
            Venda.status == 'finalizada'
        ).order_by(Venda.data_venda.desc()).limit(10).all()
        
        if not sales:
            print("Nenhuma venda encontrada.")
        else:
            print(f"Últimas 10 vendas:")
            for s in sales:
                print(f" - {s.data_venda}")

if __name__ == "__main__":
    check_dates()
