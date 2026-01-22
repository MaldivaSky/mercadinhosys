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
    
    # Test produtos/estoque endpoint with search
    produtos_url = "http://127.0.0.1:5000/api/produtos/estoque"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Search for "ar"
    print("\n📦 Testando busca por 'ar'...")
    params = {"pagina": 1, "por_pagina": 50, "busca": "ar", "ativos": "true", "ordenar_por": "nome", "direcao": "asc"}
    response = requests.get(produtos_url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Encontrados: {len(data.get('produtos', []))} produtos")
        print(f"Estatísticas: {json.dumps(data.get('estatisticas', {}), indent=2)}")
        
        if data.get('produtos'):
            print(f"\nPrimeiros 3 produtos:")
            for p in data['produtos'][:3]:
                print(f"  - {p['nome']} (Estoque: {p['quantidade']}, Fornecedor: {p.get('fornecedor_nome', 'N/A')})")
    else:
        print(f"❌ Erro: {response.text}")
    
    # Test 2: Search for "co"
    print("\n📦 Testando busca por 'co'...")
    params = {"pagina": 1, "por_pagina": 50, "busca": "co", "ativos": "true", "ordenar_por": "nome", "direcao": "asc"}
    response = requests.get(produtos_url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Encontrados: {len(data.get('produtos', []))} produtos")
        
        if data.get('produtos'):
            print(f"\nPrimeiros 3 produtos:")
            for p in data['produtos'][:3]:
                print(f"  - {p['nome']} (Estoque: {p['quantidade']}, Fornecedor: {p.get('fornecedor_nome', 'N/A')})")
    else:
        print(f"❌ Erro: {response.text}")
else:
    print(f"❌ Erro no login: {login_response.text}")
