"""
Fix ALL VARCHAR no Neon PostgreSQL
Aumenta TODOS os VARCHAR pequenos para 255
"""
import os
import sys

# Usar DATABASE_URL do .env
if not os.environ.get('DATABASE_URL'):
    print("❌ ERRO: DATABASE_URL não configurada no .env")
    print("Configure suas credenciais Neon em backend/.env")
    sys.exit(1)

if 'SQLITE_DB' in os.environ:
    del os.environ['SQLITE_DB']

from app import create_app, db
from sqlalchemy import text

print("=" * 60)
print("🔧 FIX ALL VARCHAR - NEON")
print("=" * 60)
print()

app = create_app()

with app.app_context():
    try:
        print("📋 Buscando todas as colunas VARCHAR pequenas...")
        print()
        
        # Buscar todas as colunas VARCHAR com tamanho <= 50
        result = db.session.execute(text("""
            SELECT 
                table_name, 
                column_name, 
                character_maximum_length
            FROM information_schema.columns
            WHERE 
                table_schema = 'public' 
                AND data_type = 'character varying'
                AND character_maximum_length IS NOT NULL
                AND character_maximum_length <= 50
            ORDER BY table_name, column_name
        """))
        
        colunas = result.fetchall()
        
        if not colunas:
            print("✅ Nenhuma coluna VARCHAR pequena encontrada!")
            sys.exit(0)
        
        print(f"🔍 Encontradas {len(colunas)} colunas VARCHAR pequenas:")
        print()
        
        for tabela, coluna, tamanho in colunas:
            print(f"   📌 {tabela}.{coluna} = VARCHAR({tamanho})")
        
        print()
        print("=" * 60)
        print("⚠️  ATENÇÃO: Vou aumentar TODAS para VARCHAR(255)")
        print("=" * 60)
        print()
        
        resposta = input("Deseja continuar? (s/N): ").lower()
        
        if resposta != 's':
            print("❌ Operação cancelada")
            sys.exit(0)
        
        print()
        print("🔄 Alterando colunas...")
        print()
        
        sucesso = 0
        erros = 0
        
        for tabela, coluna, tamanho_atual in colunas:
            try:
                print(f"   🔄 {tabela}.{coluna} ({tamanho_atual} → 255)...", end=" ")
                
                db.session.execute(text(f"""
                    ALTER TABLE {tabela} 
                    ALTER COLUMN {coluna} TYPE VARCHAR(255)
                """))
                
                db.session.commit()
                print("✅")
                sucesso += 1
                
            except Exception as e:
                print(f"❌ {str(e)[:50]}")
                erros += 1
                db.session.rollback()
        
        print()
        print("=" * 60)
        print(f"✅ CONCLUÍDO!")
        print("=" * 60)
        print(f"   Sucesso: {sucesso}")
        print(f"   Erros:   {erros}")
        print("=" * 60)
        print()
        
        if sucesso > 0:
            print("🚀 Agora execute: python seed_neon.py")
        
        print()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)
