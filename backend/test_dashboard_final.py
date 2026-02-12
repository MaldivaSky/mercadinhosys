import sys
import os
import traceback
from datetime import datetime

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.dashboard_cientifico.orchestration import DashboardOrchestrator
from app.models import Estabelecimento

def test_dashboard():
    app = create_app()
    with app.app_context():
        print("🚀 INICIANDO TESTE DE DEBBUG DO DASHBOARD CIENTÍFICO")
        print("=" * 60)
        
        # Pegar o primeiro estabelecimento disponível
        estab = db.session.query(Estabelecimento).first()
        if not estab:
            print("❌ NENHUM ESTABELECIMENTO ENCONTRADO NO BANCO")
            return
            
        print(f"🏢 TESTANDO PARA ESTABELECIMENTO: {estab.id} - {estab.nome_fantasia}")
        
        try:
            orchestrator = DashboardOrchestrator(estab.id)
            print("🔍 Chamando get_scientific_dashboard(days=30)...")
            
            # Forçar bypass do cache se necessário ou apenas chamar a lógica direta
            # Se quisermos ver o erro real, chamamos a lógica privada
            data = orchestrator._get_scientific_dashboard_logic(days=30)
            
            print("✅ DASHBOARD GERADO COM SUCESSO!")
            # print(f"📊 Resumo dos dados: {list(data.keys())}")
            
        except Exception as e:
            print("❌ ERRO CAPTURADO DURANTE A GERAÇÃO DO DASHBOARD:")
            print("-" * 60)
            print(f"Tipo do erro: {type(e).__name__}")
            print(f"Mensagem: {str(e)}")
            print("-" * 60)
            traceback.print_exc()
            print("-" * 60)

if __name__ == "__main__":
    test_dashboard()
