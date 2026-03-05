import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.dashboard_cientifico import DashboardOrchestrator
import traceback

app = create_app()

with app.app_context():
    print("Iniciando teste manual do Dashboard")
    try:
        # Pega o primeiro estabelecimento
        from app.models import Estabelecimento
        est = Estabelecimento.query.first()
        if not est:
            print("Nenhum estabelecimento encontrado.")
            sys.exit(1)
            
        print(f"Testando para Estabelecimento ID: {est.id}")
        
        orchestrator = DashboardOrchestrator(establishment_id=est.id)
        data = orchestrator.get_scientific_dashboard(days=30)
        
        print("Success:", data.get('success'))
        if not data.get('success'):
            print("Error payload:", data.get('error'))
            
    except Exception as e:
        print("EXCEPTION OCORRIDA:")
        traceback.print_exc()
