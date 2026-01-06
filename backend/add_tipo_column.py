"""Script para adicionar coluna tipo na tabela produtos"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Tentar adicionar a coluna
        db.session.execute(text('ALTER TABLE produtos ADD COLUMN tipo VARCHAR(30) DEFAULT "unidade"'))
        db.session.commit()
        print('✅ Coluna tipo adicionada com sucesso!')
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print('⚠️ Coluna tipo já existe!')
        else:
            print(f'❌ Erro: {e}')
            raise
