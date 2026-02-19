
import sys
import os
import logging
from sqlalchemy import func

# Add backend directory to path
sys.path.append(os.getcwd())

from app import create_app
from app.models import db, Venda

# Configure logging
logging.basicConfig(level=logging.INFO)

def check_venda_ids():
    app = create_app()
    with app.app_context():
        print("--- Verificando IDs de Estabelecimento em Vendas ---")
        try:
            # Count sales by establishment_id
            results = db.session.query(
                Venda.estabelecimento_id, 
                func.count(Venda.id)
            ).group_by(Venda.estabelecimento_id).all()
            
            print(f"Distribuição de Vendas por Estabelecimento:")
            for est_id, count in results:
                print(f"  ID: {est_id} -> {count} vendas")
                
            # Check total finalizada
            total_finalizada = Venda.query.filter_by(status='finalizada').count()
            print(f"Total de Vendas Finalizadas: {total_finalizada}")
            
        except Exception as e:
            print(f"Erro ao consultar DB: {e}")

if __name__ == "__main__":
    check_venda_ids()
