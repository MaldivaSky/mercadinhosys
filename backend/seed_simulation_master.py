import os
import sys
import time
import argparse
from datetime import datetime, date, timedelta
from sqlalchemy import text

# 1. SETUP PATHS
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# 2. LOAD ENV
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

os.environ["FLASK_ENV"] = "simulation"
os.environ["SYNC_ENABLED"] = "false"
os.environ["SKIP_SYNC_LISTENERS"] = "1" 
os.environ["SKIP_AUDIT_LOGS"] = "1"

from app import create_app
from app.models import db
from app.simulation.master_seeder_logic import MasterSeeder

def run_cloud_sync(app):
    """Executa a sincronização híbrida com a nuvem (Aiven)"""
    aiven_url = os.environ.get("AIVEN_DATABASE_URL")
    if not aiven_url:
        print("\n[SYNC] ⚠️ AIVEN_DATABASE_URL não configurada. Sync abortado.")
        return

    print("\n[SYNC] Sincronizando com a Nuvem (Aiven)...")
    try:
        from scripts.force_sync_to_aiven import force_sync
        res = force_sync(app=app)
        if res.get("success"):
            print(f"[SYNC] ✅ {res.get('total_registros')} registros sincronizados.")
        else:
            print(f"[SYNC] ⚠️ Falha na sincronia: {res.get('erro')}")
    except Exception as e:
        print(f"[SYNC] ❌ Erro: {e}")

def run_simulation(app):
    """Executa o processo de sementeira local"""
    with app.app_context():
        print("\n" + "="*70)
        print(" 🧠 [HIERARCHICAL ENGINE] MERCADINHOSYS MASTER SIMULATION")
        print("="*70)
        
        # A. RESET LOCAL (Docker)
        print("\n[LOCAL] Resetando banco de dados...")
        db.drop_all()
        db.create_all()
        db.session.commit()
        print("[LOCAL] ✅ Banco Resetado.")

        # B. MASTER SEEDER (Hierárquico via ORM)
        print("\n[MASTER] Iniciando Geração Hierárquica de 6 Meses...")
        try:
            # Semeia a estrutura base e a simulação de 6 meses
            MasterSeeder.run_master_generation(app, months=6)
            print("\n[MASTER] ✅ Geração Concluída com Sucesso!")
        except Exception as e:
            print(f"\n[MASTER] ❌ ERRO NA GERAÇÃO: {e}")
            import traceback
            traceback.print_exc()
            return

        print("\n" + "="*70)
        print(" 🎉 [LOCAL SEED] OPERAÇÃO LOCAL CONCLUÍDA")
        print("="*70)

def main():
    parser = argparse.ArgumentParser(description="Simulação Master do MercadinhoSys")
    parser.add_argument('--sync-cloud', action='store_true',
                        help='Sincronizar com nuvem após seed local')
    args = parser.parse_args()
    
    app = create_app()
    
    run_simulation(app)  # sempre executa seed local
    
    if args.sync_cloud:
        run_cloud_sync(app)  # apenas se explicitamente solicitado

if __name__ == '__main__':
    main()
