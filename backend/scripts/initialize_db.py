import os
import sys
from app import create_app, db

def initialize_database():
    app = create_app()
    with app.app_context():
        print("🚀 Iniciando reconstrução do banco de dados (Especialista ERP)...")
        
        # O banco já foi deletado no passo anterior pelo comando shell,
        # mas garantimos aqui por segurança.
        db_path = 'instance/mercadinho_local.db'
        if os.path.exists(db_path):
            print(f"⚠️  Aviso: O banco {db_path} ainda existe. Removendo...")
            os.remove(db_path)
            
        print("🏗️  Criando todas as tabelas a partir dos modelos reconstruídos...")
        db.create_all()
        
        # Verificar se as tabelas foram criadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✅ Tabelas criadas com sucesso: {len(tables)}")
        print(f"📋 Lista: {tables}")
        
        # Verificar se sync_uuid existe em VendaItem e Caixa como teste
        for table in ['venda_itens', 'caixas', 'movimentacoes_estoque']:
            if table in tables:
                cols = [c['name'] for c in inspector.get_columns(table)]
                if 'sync_uuid' in cols:
                    print(f"✨ Integridade: Tabela '{table}' possui 'sync_uuid'.")
                else:
                    print(f"❌ Erro: Tabela '{table}' NÃO possui 'sync_uuid'!")
        
        print("\n✅ Reconstrução finalizada com sucesso!")

if __name__ == "__main__":
    initialize_database()
