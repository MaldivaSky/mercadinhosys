import requests
import json

# Login first
login_url = "http://127.0.0.1:5000/api/auth/login"
login_data = {"username": "admin", "senha": "admin123"}

print("🔐 Fazendo login...")
login_response = requests.post(login_url, json=login_data)

if login_response.status_code == 200:
    token = login_response.json()["data"]["access_token"]
    print(f"✅ Token obtido")
    
    # Test categorias endpoint
    categorias_url = "http://127.0.0.1:5000/api/produtos/categorias"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"ativos": "true"}
    
    print("\n📦 Testando endpoint /api/produtos/categorias...")
    response = requests.get(categorias_url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sucesso!")
        print(f"Categorias: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Erro: {response.text}")
else:
    print(f"❌ Erro no login: {login_response.text}")
