import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # Cria token de super admin
    # Baseado na autenticação, o sub pode ser o id do usuário e is_super_admin=True
    access_token = create_access_token(
        identity="1",
        additional_claims={
            "is_super_admin": True,
            "estabelecimento_id": None
        }
    )
    
    client = app.test_client()
    
    # 1. Teste com Header X-Establishment-ID = "all"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Establishment-ID": "all"
    }
    
    print("Testing GET /api/dashboard/cientifico?days=30 with X-Establishment-ID: all")
    response = client.get('/api/dashboard/cientifico?days=30', headers=headers)
    print("Status:", response.status_code)
    try:
        print("Data:", response.get_json())
    except Exception as e:
        print("Raw Data:", response.data.decode('utf-8'))
    
    print("\n------------------------------\n")
    
    # 2. Teste sem Header (deve quebrar se establishment não for passado? Não, espera falhar de outra forma)
    headers2 = {
        "Authorization": f"Bearer {access_token}"
    }
    print("Testing GET /api/dashboard/cientifico?days=30 with NO header")
    response2 = client.get('/api/dashboard/cientifico?days=30', headers=headers2)
    print("Status:", response2.status_code)
    try:
        print("Data:", response2.get_json())
    except Exception as e:
        print("Raw Data:", response2.data.decode('utf-8'))
