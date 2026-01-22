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
    
    # Test CSV export endpoint
    csv_url = "http://127.0.0.1:5000/api/produtos/exportar/csv"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"ativos": "true"}
    
    print("\n📦 Testando endpoint /api/produtos/exportar/csv...")
    response = requests.get(csv_url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sucesso!")
        print(f"Total de produtos exportados: {data.get('total_produtos', 0)}")
        
        # Show first 3 lines of CSV
        csv_lines = data.get('csv', '').split('\n')
        print(f"\nPrimeiras 3 linhas do CSV:")
        for line in csv_lines[:3]:
            print(f"  {line}")
    else:
        print(f"❌ Erro: {response.text}")
else:
    print(f"❌ Erro no login: {login_response.text}")
