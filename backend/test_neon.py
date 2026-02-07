from sqlalchemy import create_engine, text

neon_url = "postgresql://neondb_owner:npg_jl8aMb4KGZBR@ep-quiet-smoke-a8z521gd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

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
