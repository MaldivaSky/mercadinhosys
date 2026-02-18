import time
import os
import sys

# Adiciona o diretório 'backend' ao sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app
from app.dashboard_cientifico.orchestration import DashboardOrchestrator

def benchmark():
    app = create_app()
    with app.app_context():
        # Simulando o estabelecimento 1 (ou o que estiver no banco)
        est_id = 1
        orchestrator = DashboardOrchestrator(est_id)
        
        print(f"🚀 Iniciando benchmark do dashboard (Est: {est_id})...")
        
        start = time.time()
        # Forçamos bypass do cache se possível ou apenas chamamos a lógica
        data = orchestrator._get_scientific_dashboard_logic(days=30)
        end = time.time()
        
        print(f"✅ Dashboard carregado em {end - start:.2f} segundos.")
        print(f"📊 Campos retornados: {list(data.keys()) if data else 'Nenhum'}")
        
        if data:
            print(f"💰 Faturamento: {data.get('financials', {}).get('revenue')}")
            print(f"📈 ROI: {data.get('financials', {}).get('roi')}%")

if __name__ == "__main__":
    benchmark()
