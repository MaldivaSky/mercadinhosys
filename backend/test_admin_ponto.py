
import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Funcionario
from flask_jwt_extended import create_access_token

def test_admin_ponto():
    app = create_app()
    client = app.test_client()
    
    with app.app_context():
        print("🔍 Iniciando Teste Admin Ponto...")
        
        # 1. Pegar Admin
        admin = Funcionario.query.filter_by(role='admin').first()
        if not admin:
            print("❌ Nenhum admin encontrado!")
            return
            
        print(f"👤 Logando como Admin: {admin.nome}")
            
        # 2. Gerar Token
        access_token = create_access_token(
            identity=str(admin.id), 
            additional_claims={
                "estabelecimento_id": admin.estabelecimento_id, 
                "role": admin.role,
                "status": "ativo"
            }
        )
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # 3. Testar /admin/todos
        url = "/api/ponto/admin/todos"
        print(f"🌐 GET {url}")
        
        response = client.get(url, headers=headers)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            total = data.get('data', {}).get('total', 0)
            print(f"✅ Sucesso! Total de registros: {total}")
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(response.get_data(as_text=True))

if __name__ == "__main__":
    test_admin_ponto()
