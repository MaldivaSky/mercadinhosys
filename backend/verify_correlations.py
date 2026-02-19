
import sys
import os
import logging
from unittest.mock import MagicMock

# Add backend directory to path
sys.path.append(os.getcwd())

# 🛑 MONKEYPATCH TO PREVENT HANGING ON DB INIT
import app
app.init_db = MagicMock()
print("🔧 Monkeypatched app.init_db to avoid hanging...", flush=True)

from app import create_app
from app.dashboard_cientifico.orchestration import DashboardOrchestrator
from app.models import db, Venda, VendaItem
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.ERROR) # Less noise

def verify_correlations():
    print("\n" + "="*60, flush=True)
    print("🔍 INICIANDO VERIFICAÇÃO DE CORRELAÇÕES (MODE: FORCE EXIT)", flush=True)
    print("="*60 + "\n", flush=True)

    os.environ['WERKZEUG_RUN_MAIN'] = 'true' 

    try:
        app = create_app()
        with app.app_context():
            
            print("⏳ Verificando conexão...", flush=True)
            # Just verify we can query
            try:
                db.session.execute("SELECT 1")
                print(f"✅ Conexão com Banco OK.", flush=True)
            except:
                print("❌ Falha no banco, mas tentando orchestrator...", flush=True)

            print("\n--- 1. Testando via Orchestrator (Establishment=1, Days=365) ---", flush=True)
            
            print("⏳ Solicitando Dashboard Científico...", flush=True)
            orchestrator = DashboardOrchestrator(1) 
            dashboard_data = orchestrator.get_scientific_dashboard(days=365)
            print("✅ Dashboard retornado!", flush=True)
            
            data_payload = dashboard_data.get('data', {})
            
            correlations = []
            if 'insights_cientificos' in data_payload and 'correlações' in data_payload['insights_cientificos']:
                correlations = data_payload['insights_cientificos']['correlações']
            elif 'correlations' in data_payload:
                correlations = data_payload['correlations']

            print(f"  🔢 Total correlações encontradas: {len(correlations)}", flush=True)
            
            print("-" * 40, flush=True)
            found_hourly = False
            found_weekly = False
            
            for i, corr in enumerate(correlations):
                v1 = corr.get('variavel1')
                v2 = corr.get('variavel2')
                r = corr.get('correlacao')
                insight = corr.get('insight')
                
                print(f"    {i+1}. [{v1}] x [{v2}] | R: {r:.2f}", flush=True)
                # print(f"       Insight: {insight}", flush=True)
                
                if "Hora" in str(v1) or "Horário" in str(v2) or "Pico" in str(v1): found_hourly = True
                if "Dia" in str(v1) or "Semana" in str(v1) or "Melhor Ticket" in str(v1): found_weekly = True

            print("-" * 40, flush=True)
            if found_hourly: print("  ✅ Correlação de HORÁRIO encontrada!", flush=True)
            else: print("  ❌ Correlação de HORÁRIO NÃO encontrada!", flush=True)
            
            if found_weekly: print("  ✅ Correlação de DIA DA SEMANA encontrada!", flush=True)
            else: print("  ❌ Correlação de DIA DA SEMANA NÃO encontrada!", flush=True)

    except Exception as e:
        print(f"❌ Erro CRÍTICO: {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60, flush=True)
    print("FIM DA VERIFICAÇÃO - FORCING EXIT", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    verify_correlations()
