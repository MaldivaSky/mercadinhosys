
import sys
import os
import json
from datetime import datetime, date
from decimal import Decimal
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Estabelecimento
from app.dashboard_cientifico.orchestration import DashboardOrchestrator

# Custom JSON encoder for Flask/SQLAlchemy types
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def debug_dashboard():
    app = create_app()
    with app.app_context():
        print("🔍 Iniciando Debug do Dashboard Científico (Com Serialização)...")
        
        est = Estabelecimento.query.first()
        if not est:
            print("❌ Nenhum estabelecimento encontrado!")
            return

        print(f"🏢 Estabelecimento: {est.nome_fantasia} (ID: {est.id})")
        
        try:
            orchestrator = DashboardOrchestrator(est.id)
            print("📊 Executando get_scientific_dashboard(days=30)...")
            
            data = orchestrator.get_scientific_dashboard(days=30)
            
            print("🔄 Tentando serializar para JSON...")
            json_str = json.dumps(data, cls=CustomEncoder)
            print(f"✅ Sucesso! JSON gerado ({len(json_str)} bytes).")
            
        except TypeError as te:
             print(f"\n❌ ERRO DE SERIALIZAÇÃO: {str(te)}")
             # Tentar achar o culpado
             import traceback
             traceback.print_exc()
        except Exception as e:
            print(f"\n❌ ERRO GERAL: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_dashboard()
