
import sys
import os
# Adicionar o diretório pai ao path para importar 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, Funcionario

app = create_app()
client = app.test_client()

with app.app_context():
    print(f"DEBUG: App using DB URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"DEBUG: MULTI_TENANT_MODE: {app.config.get('MULTI_TENANT_MODE')}")
    
    # Teste de Login via API
    payload = {
        "identifier": "maldivas",
        "senha": "Mald1v@$"
    }
    print(f"DEBUG: Attempting login with: {payload}")
    response = client.post("/api/auth/login", json=payload)
    
    print(f"DEBUG: Response Status: {response.status_code}")
    data = response.get_json()
    print(f"DEBUG: Response Data keys: {data.keys() if data else 'None'}")
    
    if data and data.get('success'):
        print("✅ Login Success")
        print(f"   Access Token exists: {bool(data.get('access_token'))}")
        print(f"   Refresh Token exists: {bool(data.get('refresh_token'))}")
        print(f"   User in data: {bool(data.get('data', {}).get('user'))}")
        
        # Testar Refresh
        print("\nDEBUG: Attempting Token Refresh...")
        refresh_token = data.get('refresh_token')
        refresh_response = client.post("/api/auth/refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        print(f"DEBUG: Refresh Status: {refresh_response.status_code}")
        refresh_data = refresh_response.get_json()
        print(f"DEBUG: Refresh Data: {refresh_data}")
    else:
        print(f"❌ Login Failed: {data.get('error') if data else 'No data'}")
