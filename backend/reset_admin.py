import os
import sys
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, Funcionario

def reset_admin_password():
    """
    Reseta a senha do usuário 'admin' para 'admin123'.
    Este script detecta automaticamente o banco configurado (Postgres/SQLite).
    """
    app = create_app()
    with app.app_context():
        admin = Funcionario.query.filter_by(username='admin').first()
        if not admin:
            print("❌ Usuário 'admin' não encontrado.")
            return
        
        # Define a nova senha
        nova_senha = "admin123"
        admin.set_senha(nova_senha)
        
        try:
            db.session.commit()
            print(f"✅ Senha do admin resetada com sucesso para: {nova_senha}")
            print(f"ℹ️  Banco de Dados: {db.engine.url.drivername}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar nova senha: {e}")

if __name__ == "__main__":
    # Garante que o diretório atual está no path para importar o módulo 'app'
    sys.path.append(os.getcwd())
    reset_admin_password()
