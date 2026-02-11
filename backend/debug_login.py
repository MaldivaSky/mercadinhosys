
import sys
import os
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Funcionario, Estabelecimento, LoginHistory

def debug_login():
    app = create_app()
    client = app.test_client()
    
    with app.app_context():
        print("🔍 Debug Login - Analisando dados...")
        
        # 1. Verificar se existe admin
        admin = Funcionario.query.filter_by(username="admin").first()
        if not admin:
            print("❌ Usuário admin NÃO encontrado!")
        else:
            print(f"✅ Usuário admin encontrado: ID={admin.id}, Username={admin.username}, Role={admin.role}, Estabelecimento={admin.estabelecimento_id}")
            print(f"   Ativo: {admin.ativo}, Status: {admin.status}")
            
            # Verificar senha
            if admin.check_senha("admin123"):
                print("✅ Senha 'admin123' está CORRETA.")
            else:
                print("❌ Senha 'admin123' está INCORRETA.")
                
            # Verificar estabelecimento
            est = Estabelecimento.query.get(admin.estabelecimento_id)
            if est:
                print(f"✅ Estabelecimento encontrado: {est.nome_fantasia} (ID: {est.id})")
            else:
                print(f"❌ Estabelecimento ID {admin.estabelecimento_id} não encontrado!")

        # 2. Tentar login via API
        print("\n🌐 Tentando login via API (/api/auth/login)...")
        payload = {
            "username": "admin",
            "senha": "admin123"
        }
        
        try:
            response = client.post("/api/auth/login", json=payload)
            print(f"📥 Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print("❌ Erro no login:")
                print(response.get_data(as_text=True))
            else:
                data = response.get_json()
                print("✅ Login via API com sucesso!")
                print(f"   Token: {data.get('data', {}).get('access_token')[:20]}...")
                
        except Exception as e:
            print(f"❌ EXCEÇÃO ao chamar API: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_login()
