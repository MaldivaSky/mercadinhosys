"""
Teste rápido para verificar se a rota de fornecedores está funcionando com JWT
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_fornecedores():
    print("🔍 Testando autenticação e rota de fornecedores...\n")
    
    # 1. Login
    print("1️⃣ Fazendo login...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(login_response.text)
        return
    
    login_data = login_response.json()
    token = login_data.get("access_token")
    print(f"✅ Login OK! Token: {token[:50]}...\n")
    
    # 2. Testar rota de fornecedores
    print("2️⃣ Testando GET /api/fornecedores...")
    headers = {"Authorization": f"Bearer {token}"}
    
    fornecedores_response = requests.get(
        f"{BASE_URL}/api/fornecedores",
        headers=headers,
        params={"por_pagina": 10}
    )
    
    print(f"Status: {fornecedores_response.status_code}")
    
    if fornecedores_response.status_code == 200:
        data = fornecedores_response.json()
        print(f"✅ Sucesso!")
        print(f"Total de fornecedores: {data.get('total', 0)}")
        print(f"Fornecedores retornados: {len(data.get('fornecedores', []))}")
        
        if data.get('fornecedores'):
            print("\n📦 Primeiro fornecedor:")
            primeiro = data['fornecedores'][0]
            print(json.dumps(primeiro, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Erro: {fornecedores_response.status_code}")
        print(fornecedores_response.text)
    
    # 3. Testar estatísticas
    print("\n3️⃣ Testando GET /api/fornecedores/estatisticas...")
    stats_response = requests.get(
        f"{BASE_URL}/api/fornecedores/estatisticas",
        headers=headers
    )
    
    print(f"Status: {stats_response.status_code}")
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"✅ Estatísticas:")
        print(json.dumps(stats.get('estatisticas', {}), indent=2, ensure_ascii=False))
    else:
        print(f"❌ Erro: {stats_response.status_code}")
        print(stats_response.text)

if __name__ == "__main__":
    try:
        test_fornecedores()
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao backend.")
        print("Certifique-se de que o servidor está rodando em http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
