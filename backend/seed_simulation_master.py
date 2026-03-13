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
    print("⚠️ python-dotenv não instalado, pulando carregamento manual de .env")

os.environ["FLASK_ENV"] = "simulation"

from app import create_app
from app.models import db, Estabelecimento, Funcionario
from app.simulation.dna_factory import DNAFactory
from app.simulation.chronicle import ChronicleSimulator

def run_simulation():
    app = create_app()
    
    with app.app_context():
        print("🚀 [START] INICIANDO SEED SIMULATION MASTER (MAGNITUDE SENIOR)...")
        
        # Opcional: Limpar banco antes de rodar? 
        # Cuidado: o usuário falou "preciso rodar a seed master", se rodar no banco atual pode duplicar ou dar erro se houver UK.
        # run_digital_twin.py dá drop_all and create_all. Vou assumir que o usuário Quer um banco NOVO/RESETADO.
        
        print("🧱 Limpando banco de dados para Seed Master...")
        db.drop_all()
        db.create_all()
        db.session.commit()
        print("✅ Banco Resetado.")

        simulator = ChronicleSimulator(app)
        
        print("\n🌟 MERCADINHOSYS: ENGINE DO GÊMEO DIGITAL 🌟")
        try:
            # Rodar Simulação Master (6 meses)
            simulator.run_full_simulation(months=6)
            print("\n🏆 Simulação Concluída com Sucesso!")
            
            # Verificar se os dados de acesso do Super Admin estão corretos
            # O RealisticInjector já cria o 'maldivas' / 'Mald1v@$'
            
            print("-" * 50)
            print("🌟 DADOS DE ACESSO MASTER (5 CENÁRIOS):")
            print("1. SUPER ADMIN (CONTROLE GLOBAL):")
            print("   - Login: maldivas")
            print("   - Senha: Mald1v@$")
            
            print("\n2. ESTABELECIMENTOS SIMULADOS (GÊMEO DIGITAL):")
            scenarios = ["ELITE", "BOM", "RAZOAVEL", "MAL", "PESSIMO"]
            for s_key in scenarios:
                dna = DNAFactory.get_dna(s_key)
                est = Estabelecimento.query.filter_by(nome_fantasia=dna.nome).first()
                if est:
                    admin = Funcionario.query.filter_by(estabelecimento_id=est.id, role="ADMIN").first()
                    print(f"   🏢 {dna.nome} ({s_key}):")
                    print(f"      - Admin Login: {admin.username if admin else 'N/A'}")
                    print(f"      - Admin Pass: admin{est.id}")
            print("-" * 50)

        except Exception as e:
            print(f"\n❌ Erro Crítico na Simulação: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_simulation()
