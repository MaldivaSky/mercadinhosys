"""
Fix NOT NULL constraints no Neon PostgreSQL
Remove NOT NULL de campos opcionais para compatibilidade com SQLite
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
print("🔧 FIX NOT NULL - NEON")
print("=" * 60)
print()

app = create_app()

with app.app_context():
    try:
        print("⚠️  Removendo NOT NULL de campos opcionais...")
        print()
        
        # Campos que devem ser nullable
        alteracoes = [
            # Clientes
            ("clientes", "cep"),
            ("clientes", "logradouro"),
            ("clientes", "numero"),
            ("clientes", "bairro"),
            ("clientes", "cidade"),
            ("clientes", "estado"),
            ("clientes", "celular"),
            ("clientes", "rg"),
            ("clientes", "data_nascimento"),
            
            # Fornecedores
            ("fornecedores", "cep"),
            ("fornecedores", "logradouro"),
            ("fornecedores", "numero"),
            ("fornecedores", "bairro"),
            ("fornecedores", "cidade"),
            ("fornecedores", "estado"),
            ("fornecedores", "inscricao_estadual"),
            ("fornecedores", "contato_nome"),
            ("fornecedores", "contato_telefone"),
        ]
        
        sucesso = 0
        erros = 0
        
        for tabela, coluna in alteracoes:
            try:
                print(f"   🔄 {tabela}.{coluna}...", end=" ")
                
                db.session.execute(text(f"""
                    ALTER TABLE {tabela} 
                    ALTER COLUMN {coluna} DROP NOT NULL
                """))
                
                db.session.commit()
                print("✅")
                sucesso += 1
                
            except Exception as e:
                erro_msg = str(e)
                if "does not exist" in erro_msg or "column" in erro_msg.lower():
                    print("⚠️  (não existe)")
                elif "not-null constraint" in erro_msg.lower():
                    print("⚠️  (já nullable)")
                else:
                    print(f"❌ {erro_msg[:50]}")
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
            print("🚀 Agora execute: python seed_neon_rapido.py")
        
        print()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)
