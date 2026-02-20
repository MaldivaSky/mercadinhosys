import os
import sys

# Adiciona o diretório raiz ao path para importar o app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import create_app, db
    from sqlalchemy import text, inspect
    
    app = create_app()
    with app.app_context():
        print("--- AUDITORIA DE BANCO DE DADOS ---")
        
        # 1. Verificar colunas da tabela 'funcionarios'
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('funcionarios')]
        
        print(f"Colunas encontradas na tabela 'funcionarios': {columns}")
        
        if 'login' in columns:
            print("✅ Coluna 'login' existe (inesperado baseado no modelo).")
        else:
            print("❌ Coluna 'login' NÃO EXISTE.")
            
        if 'username' in columns:
            print("✅ Coluna 'username' existe conforme definido no modelo.")
        else:
            print("❌ Coluna 'username' NÃO EXISTE (problema crítico de esquema).")

        # 2. Simular a query que estava falhando em query_helpers.py
        print("\nSimulando query original (SELECT login...):")
        try:
            db.session.execute(text("SELECT id, nome, email, login FROM funcionarios LIMIT 1")).fetchone()
            print("✅ Query funcionou (surpreendente).")
        except Exception as e:
            print(f"❌ Query falhou como previsto: {str(e)}")

        # 3. Simular a query corrigida (SELECT username...):
        print("\nSimulando query corrigida (SELECT username...):")
        try:
            db.session.execute(text("SELECT id, nome, email, username FROM funcionarios LIMIT 1")).fetchone()
            print("✅ Query corrigida funcionou com sucesso!")
        except Exception as e:
            print(f"❌ Query corrigida também falhou: {str(e)}")

except Exception as e:
    print(f"Erro ao executar auditoria: {e}")
