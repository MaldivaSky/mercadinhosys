import os
import sys
import sqlalchemy as sa
from sqlalchemy import text
from app import create_app
from app.models import db

def sync_cloud_schema():
    """
    Sincroniza a estrutura do banco de dados na nuvem (Aiven/Render)
    sem deletar dados existentes. Adiciona colunas que podem estar faltando.
    """
    print("🚀 Iniciando sincronização SEGURA de esquema...")
    
    app = create_app()
    with app.app_context():
        engine = db.engine
        inspector = sa.inspect(engine)
        
        # 1. Verificar/Criar Tabelas que não existem
        print("🔍 Verificando tabelas faltantes...")
        db.create_all()
        
        # 2. Adicionar Colunas Faltantes em tabelas existentes (Manual Upgrade)
        # SQLAlchemy create_all não adiciona colunas a tabelas já existentes.
        
        updates = [
            # Tabela: estabelecimentos
            ('estabelecimentos', 'plano', 'VARCHAR(20) DEFAULT \'Basic\''),
            ('estabelecimentos', 'plano_status', 'VARCHAR(20) DEFAULT \'experimental\''),
            ('estabelecimentos', 'vencimento_assinatura', 'TIMESTAMP'),
            ('estabelecimentos', 'pagarme_id', 'VARCHAR(100)'),
            # Tabela: configuracoes
            ('configuracoes', 'logo_base64', 'TEXT'),
            ('configuracoes', 'arredondamento_valores', 'BOOLEAN DEFAULT TRUE'),
            ('configuracoes', 'dias_alerta_validade', 'INTEGER DEFAULT 30'),
            ('configuracoes', 'estoque_minimo_padrao', 'INTEGER DEFAULT 10'),
        ]
        
        with engine.connect() as conn:
            for table, column, col_type in updates:
                columns = [c['name'] for c in inspector.get_columns(table)]
                if column not in columns:
                    print(f"➕ Adicionando coluna '{column}' na tabela '{table}'...")
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                        conn.commit()
                        print(f"✅ Coluna '{column}' adicionada!")
                    except Exception as e:
                        print(f"⚠️ Erro ao adicionar {column}: {e}")
                else:
                    print(f"✔️ Coluna '{column}' já existe em '{table}'.")

        print("\n✨ Sincronização concluída com sucesso!")
        print(f"📡 Banco Conectado: {engine.url.drivername} (Host: {engine.url.host})")

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    sync_cloud_schema()
