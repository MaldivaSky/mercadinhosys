"""
Fix Neon PostgreSQL Schema
Corrige tamanhos de VARCHAR e adiciona colunas faltantes
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
print("🔧 FIX NEON SCHEMA - COMPLETO")
print("=" * 60)
print()

app = create_app()

with app.app_context():
    try:
        print("📋 Corrigindo schema do banco...")
        print()
        
        # 1. Adicionar coluna status se não existir
        print("1️⃣ Verificando coluna 'status'...")
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='funcionarios' AND column_name='status'
        """))
        
        if result.fetchone() is None:
            print("   ➕ Adicionando coluna 'status'...")
            db.session.execute(text("""
                ALTER TABLE funcionarios 
                ADD COLUMN status VARCHAR(20) DEFAULT 'ativo'
            """))
            db.session.commit()
            print("   ✅ Coluna 'status' adicionada")
        else:
            print("   ✅ Coluna 'status' já existe")
        
        # 2. Aumentar tamanho dos campos VARCHAR
        print()
        print("2️⃣ Aumentando tamanho dos campos VARCHAR...")
        
        alteracoes = [
            ("funcionarios", "telefone", "VARCHAR(20)"),
            ("funcionarios", "celular", "VARCHAR(20)"),
            ("funcionarios", "cpf", "VARCHAR(20)"),
            ("funcionarios", "rg", "VARCHAR(20)"),
            ("funcionarios", "cep", "VARCHAR(10)"),
            ("funcionarios", "bairro", "VARCHAR(100)"),
            ("funcionarios", "cidade", "VARCHAR(100)"),
            ("clientes", "telefone", "VARCHAR(20)"),
            ("clientes", "celular", "VARCHAR(20)"),
            ("clientes", "cpf", "VARCHAR(20)"),
            ("clientes", "rg", "VARCHAR(20)"),
            ("clientes", "cep", "VARCHAR(10)"),
            ("clientes", "bairro", "VARCHAR(100)"),
            ("clientes", "cidade", "VARCHAR(100)"),
            ("fornecedores", "telefone", "VARCHAR(20)"),
            ("fornecedores", "cnpj", "VARCHAR(20)"),
            ("fornecedores", "cep", "VARCHAR(10)"),
            ("fornecedores", "bairro", "VARCHAR(100)"),
            ("fornecedores", "cidade", "VARCHAR(100)"),
            ("estabelecimentos", "telefone", "VARCHAR(20)"),
            ("estabelecimentos", "cnpj", "VARCHAR(20)"),
            ("estabelecimentos", "cep", "VARCHAR(10)"),
            ("estabelecimentos", "bairro", "VARCHAR(100)"),
            ("estabelecimentos", "cidade", "VARCHAR(100)"),
        ]
        
        for tabela, coluna, novo_tipo in alteracoes:
            try:
                print(f"   🔄 {tabela}.{coluna} → {novo_tipo}")
                db.session.execute(text(f"""
                    ALTER TABLE {tabela} 
                    ALTER COLUMN {coluna} TYPE {novo_tipo}
                """))
                db.session.commit()
            except Exception as e:
                if "does not exist" in str(e):
                    print(f"   ⚠️  Coluna {tabela}.{coluna} não existe (OK)")
                else:
                    print(f"   ⚠️  Erro em {tabela}.{coluna}: {e}")
        
        print("   ✅ Campos VARCHAR aumentados")
        
        # 3. Adicionar colunas que podem faltar
        print()
        print("3️⃣ Adicionando colunas opcionais...")
        
        colunas_opcionais = [
            ("funcionarios", "data_demissao", "DATE"),
            ("funcionarios", "observacoes", "TEXT"),
        ]
        
        for tabela, coluna, tipo in colunas_opcionais:
            result = db.session.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='{tabela}' AND column_name='{coluna}'
            """))
            
            if result.fetchone() is None:
                print(f"   ➕ Adicionando {tabela}.{coluna}...")
                db.session.execute(text(f"""
                    ALTER TABLE {tabela} 
                    ADD COLUMN {coluna} {tipo}
                """))
                db.session.commit()
                print(f"   ✅ Coluna {coluna} adicionada")
        
        print()
        print("=" * 60)
        print("✅ SCHEMA CORRIGIDO COM SUCESSO!")
        print("=" * 60)
        print()
        print("🚀 Agora execute: python seed_neon.py")
        print()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)
