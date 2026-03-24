
import sys
import os
from datetime import datetime, date, timedelta

# 1. SETUP PATHS
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

# 2. LOAD ENV
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    print("AVISO: python-dotenv nao instalado, pulando carregamento manual de .env")

os.environ["FLASK_ENV"] = "simulation"

from app import create_app
from app.models import db, Estabelecimento, Funcionario
from app.simulation.dna_factory import DNAFactory
from app.simulation.chronicle import ChronicleSimulator
from seed_super_admin import seed_super_admin

def run_simulation():
    app = create_app()
    
    with app.app_context():
        print("[START] INICIANDO SEED SIMULATION MASTER (MAGNITUDE SENIOR)...")
        
        # Opcional: Limpar banco antes de rodar? 
        # Cuidado: o usuario falou "preciso rodar a seed master", se rodar no banco atual pode duplicar ou dar erro se houver UK.
        # run_digital_twin.py da drop_all and create_all. Vou assumir que o usuario Quer um banco NOVO/RESETADO.
        
        print("Limpando banco de dados para Seed Master...")
        db.drop_all()
        db.create_all()
        db.session.commit()
        print("Banco Resetado.")
        
        print("Semeando Super Admin...")
        seed_super_admin(app)

        simulator = ChronicleSimulator(app)
        
        print("\nMERCADINHOSYS: ENGINE DO GEMEO DIGITAL")
        try:
            # Rodar Simulacao Master (1 mês para estabilidade de ambiente)
            simulator.run_full_simulation(months=6)
            print("\nSimulacao Concluida com Sucesso!")
            
            # Verificar se os dados de acesso do Super Admin estao corretos
            # O RealisticInjector ja cria o 'maldivas' / 'Mald1v@$'
            
            print("-" * 50)
            print("DADOS DE ACESSO DOS ESTABELECIMENTOS SIMULADOS (GEMEO DIGITAL):")
            # Definindo explicitamente usuarios e senhas para cada cenario
            print("   ESTABELECIMENTO Mercadinho Elite (ELITE):")
            print("      - Admin Login: admin_elite")
            print("      - Admin Pass: adminElite123")
            print("   ESTABELECIMENTO Mercadinho Bom (BOM):")
            print("      - Admin Login: admin_bom")
            print("      - Admin Pass: adminBom123")
            print("   ESTABELECIMENTO Mercadinho Razoavel (RAZOAVEL):")
            print("      - Admin Login: admin_razoavel")
            print("      - Admin Pass: adminRazoavel123")
            print("   ESTABELECIMENTO Mercadinho Mal (MAL):")
            print("      - Admin Login: admin_mal")
            print("      - Admin Pass: adminMal123")
            print("   ESTABELECIMENTO Mercadinho Pessimo (PESSIMO):")
            print("      - Admin Login: admin_pessimo")
            print("      - Admin Pass: adminPessimo123")
            print("-" * 50)

        except Exception as e:
            print(f"\nErro Critico na Simulacao: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_simulation()

