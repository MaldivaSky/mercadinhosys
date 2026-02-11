
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

def test_pdv_config():
    app = create_app()
    client = app.test_client()
    
    with app.app_context():
        print("🔍 Iniciando Teste PDV Configurações...")
        
        # 1. Pegar Funcionário
        func = Funcionario.query.first()
        if not func:
            print("❌ Nenhum funcionário encontrado!")
            return
            
        print(f"👤 Logando como: {func.nome}")
            
        # 2. Gerar Token
        access_token = create_access_token(
            identity=str(func.id), 
            additional_claims={
                "estabelecimento_id": func.estabelecimento_id, 
                "role": func.role,
                "status": "ativo"
            }
        )
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # 3. Testar Configurações
        url = "/api/pdv/configuracoes"
        print(f"🌐 GET {url}")
        
        response = client.get(url, headers=headers)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Sucesso! Configurações carregadas.")
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(response.get_data(as_text=True))
            
        # 4. Testar Estatísticas Rápidas
        url_stats = "/api/pdv/estatisticas-rapidas"
        print(f"🌐 GET {url_stats}")
        
        response_stats = client.get(url_stats, headers=headers)
        print(f"📥 Status Code: {response_stats.status_code}")
        
        if response_stats.status_code == 200:
             print("✅ Sucesso! Estatísticas carregadas.")
        else:
             print(f"❌ ERRO: {response_stats.status_code}")
             print(response_stats.get_data(as_text=True))

if __name__ == "__main__":
    test_pdv_config()
