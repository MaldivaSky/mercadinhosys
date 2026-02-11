#!/usr/bin/env python3
"""
Script para adicionar a coluna 'tipo' à tabela produtos.
Execute: python add_tipo_column.py
"""

import os
import sys

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text, inspect

def add_tipo_column():
    """Adiciona a coluna tipo à tabela produtos se não existir"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Verificar se a tabela existe
            if not inspector.has_table("produtos"):
                print("❌ Tabela 'produtos' não existe!")
                return False
            
            # Verificar se a coluna já existe
            columns = {col['name'] for col in inspector.get_columns('produtos')}
            
            if 'tipo' in columns:
                print("✅ Coluna 'tipo' já existe na tabela produtos")
                return True
            
            # Detectar tipo de banco
            is_sqlite = db.engine.name == 'sqlite'
            
            # Adicionar coluna
            print("🔄 Adicionando coluna 'tipo' à tabela produtos...")
            
            if is_sqlite:
                db.session.execute(text("ALTER TABLE produtos ADD COLUMN tipo VARCHAR(50)"))
            else:
                # PostgreSQL
                db.session.execute(text("ALTER TABLE produtos ADD COLUMN tipo VARCHAR(50)"))
            
            db.session.commit()
            print("✅ Coluna 'tipo' adicionada com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = add_tipo_column()
    sys.exit(0 if success else 1)
