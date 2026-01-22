"""
Seed Script para Neon PostgreSQL
Executa localmente mas popula o banco na nuvem
"""
import os
import sys

# Forçar uso do Neon PostgreSQL (lê do .env)
if not os.environ.get('DATABASE_URL'):
    print("❌ ERRO: DATABASE_URL não configurada no .env")
    print("Configure suas credenciais Neon em backend/.env")
    sys.exit(1)

# Remover SQLITE_DB para garantir que use PostgreSQL
if 'SQLITE_DB' in os.environ:
    del os.environ['SQLITE_DB']

print("=" * 60)
print("🌐 SEED NEON POSTGRESQL")
print("=" * 60)
print(f"📊 Database: Neon PostgreSQL (nuvem)")
print(f"🔗 Lendo credenciais de: backend/.env")
print("=" * 60)
print()

# Importar seed_test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        print("⚠️  ATENÇÃO: Você está prestes a semear o banco NEON (nuvem)!")
        print("⚠️  Isso irá criar/substituir dados no PostgreSQL de produção.")
        print()
        
        resposta = input("Deseja continuar? (s/N): ").lower()
        
        if resposta != 's':
            print("❌ Seed cancelado pelo usuário")
            sys.exit(0)
        
        print()
        print("🚀 Executando seed_test.py com Neon PostgreSQL...")
        print()
        
        # Executar seed_test com --reset
        import subprocess
        result = subprocess.run(
            [sys.executable, 'seed_test.py', '--reset'],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print()
            print("=" * 60)
            print("✅ SEED NEON COMPLETO!")
            print("=" * 60)
            print()
            print("📝 Credenciais de acesso:")
            print("  Username: admin")
            print("  Password: admin123")
            print()
            print("🌐 Banco: Neon PostgreSQL (nuvem)")
            print("=" * 60)
        else:
            print()
            print("❌ Erro ao executar seed")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
