"""
Adicionar coluna token_hash na tabela login_history
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get('DATABASE_URL'):
    print("❌ ERRO: DATABASE_URL não configurada no .env")
    sys.exit(1)

if 'SQLITE_DB' in os.environ:
    del os.environ['SQLITE_DB']

from app import create_app, db
from sqlalchemy import text

print("=" * 60)
print("🔧 FIX LOGIN_HISTORY - Adicionar token_hash")
print("=" * 60)
print()

app = create_app()

with app.app_context():
    try:
        print("📋 Verificando se coluna token_hash existe...")
        
        # Verificar se a coluna já existe
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='login_history' 
            AND column_name='token_hash'
        """))
        
        if result.fetchone():
            print("✅ Coluna token_hash já existe!")
            sys.exit(0)
        
        print("⚠️  Coluna token_hash não existe. Adicionando...")
        
        # Adicionar coluna token_hash
        db.session.execute(text("""
            ALTER TABLE login_history 
            ADD COLUMN token_hash INTEGER
        """))
        
        db.session.commit()
        
        print("✅ Coluna token_hash adicionada com sucesso!")
        print()
        print("=" * 60)
        print("🎉 MIGRAÇÃO CONCLUÍDA!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)
