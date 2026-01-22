import requests
import json

# Login first
login_url = "http://127.0.0.1:5000/api/auth/login"
login_data = {"username": "admin", "senha": "admin123"}

print("🔐 Fazendo login...")
login_response = requests.post(login_url, json=login_data)
print(f"Status: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json()["data"]["access_token"]
    print(f"✅ Token obtido: {token[:50]}...")
    
    # Test produtos/estoque endpoint
    produtos_url = "http://127.0.0.1:5000/api/produtos/estoque"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"pagina": 1, "por_pagina": 10, "ativos": "true"}
    
    print("\n📦 Testando endpoint /api/produtos/estoque...")
    produtos_response = requests.get(produtos_url, headers=headers, params=params)
    print(f"Status: {produtos_response.status_code}")
    
    if produtos_response.status_code == 200:
        data = produtos_response.json()
        print(f"✅ Sucesso!")
        print(f"Total de produtos: {data.get('paginacao', {}).get('total_itens', 0)}")
        print(f"Estatísticas: {json.dumps(data.get('estatisticas', {}), indent=2)}")
        
        if data.get('produtos'):
            print(f"\nPrimeiro produto:")
            print(json.dumps(data['produtos'][0], indent=2))
    else:
        print(f"❌ Erro: {produtos_response.text}")
else:
    print(f"❌ Erro no login: {login_response.text}")
