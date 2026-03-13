import sys
import os
import shutil

# 1. CAMINHO DO BANCO TEMPORÁRIO (Expert Isolated Path)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
os.makedirs(TMP_DIR, exist_ok=True)

SIM_DB_PATH = os.path.join(TMP_DIR, 'simulation_master.db')
DATABASE_URI = f"sqlite:///{SIM_DB_PATH}"

# 2. BLINDAGEM DE AMBIENTE (Expert Lockdown)
# Forçar TODAS as chaves possíveis para o SQLite local, evitando vazamento do .env (Aiven/Postgres)
db_keys = [
    "AIVEN_DATABASE_URL", "POSTGRES_URL", "DATABASE_URL_TARGET", 
    "DB_PRIMARY", "DATABASE_URL", "MAIN_DATABASE_URL", "POSTGRES_URL_NON_POOLING"
]
for key in db_keys:
    os.environ[key] = DATABASE_URI

os.environ["FLASK_ENV"] = "simulation"
os.environ["HYBRID_MODE"] = "offline"
os.environ["CLOUD_ENABLED"] = "false"
os.environ["SKIP_DB_SETUP"] = "false"

# Adicionar o diretório raiz ao path
sys.path.append(BASE_DIR)

from app import create_app
from app.models import db
from app.simulation.chronicle import ChronicleSimulator

def main():
    if os.path.exists(SIM_DB_PATH):
        try:
            os.remove(SIM_DB_PATH)
            print(f"🗑️ Limpeza de banco de simulação anterior.")
        except Exception:
            pass

    # Inicializar App com URI Forçada
    app = create_app()
    
    # Garantia Adicional: Sobrescrever config após load_dotenv interno
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    app.config["USING_POSTGRES"] = False
    
    with app.app_context():
        print(f"🧱 Master Schema: Construindo Muralha Local em: {SIM_DB_PATH}")
        db.drop_all()
        db.create_all()
        db.session.commit()
        print("✅ Schema MASTER Pronto.")

    simulator = ChronicleSimulator(app)
    
    print("\n🌟 MERCADINHOSYS: INICIANDO ENGINE DO GÊMEO DIGITAL (MAGNITUDE MASTER) 🌟")
    print(f"Modo: EXPERT ISOLATED | DB: {SIM_DB_PATH}\n")
    
    try:
        # Rodar Simulação Master (6 meses)
        simulator.run_full_simulation(months=6)
        print("\n🏆 Simulação Concluída com Magnitude Senior!")
        print(f"📊 Os dados estão prontos para análise no banco MASTER.")
        
    except Exception as e:
        print(f"\n❌ Erro Crítico na Simulação: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
