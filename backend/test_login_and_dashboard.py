import requests
import json

BASE_URL = "http://localhost:5000/api"

# 1. Fazer login
print("1. Fazendo login...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@empresa.com",
    "senha": "admin123"
})

print(f"Status: {login_response.status_code}")
print(f"Response: {json.dumps(login_response.json(), indent=2)}")

if login_response.status_code == 200:
    token = login_response.json().get("data", {}).get("access_token")
    print(f"\n✅ Token obtido: {token[:50]}...")
    
    # 2. Testar dashboard científico
    print("\n2. Testando dashboard científico...")
    headers = {"Authorization": f"Bearer {token}"}
    dashboard_response = requests.get(f"{BASE_URL}/dashboard/cientifico", headers=headers)
    
    print(f"Status: {dashboard_response.status_code}")
    if dashboard_response.status_code == 200:
        print("✅ Dashboard funcionando!")
        data = dashboard_response.json()
        print(f"Keys: {list(data.keys())}")
    else:
        print(f"❌ Erro: {dashboard_response.text}")
else:
    print("❌ Login falhou!")
