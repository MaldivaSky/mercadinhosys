import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
neon_url = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not neon_url:
    print("❌ Configure AIVEN_DATABASE_URL ou DATABASE_URL no .env")
    exit(1)
if neon_url.startswith("postgres://"):
    neon_url = neon_url.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(neon_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Conectado ao Neon")
    
    # Verificar dados
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) as total FROM registros_ponto"))
        ponto_count = result.scalar() or 0
        print(f"RegistroPonto: {ponto_count}")
        
        result = conn.execute(text("SELECT COUNT(*) as total FROM configuracoes_horario"))
        config_count = result.scalar() or 0
        print(f"ConfiguracaoHorario: {config_count}")
    
    if ponto_count == 0:
        print("\n⚠️  Neon vazio! Execute: python seed_neon_rapido.py")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
