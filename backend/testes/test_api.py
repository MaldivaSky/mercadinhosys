import requests
import json

url = "http://localhost:5000/api/auth/login"
payload = {
    "username": "admin",
    "senha": "admin123",
    "estabelecimento_id": 4,  # Usar o ID correto!
}

print("🔐 Testando login com estabelecimento_id correto...")
response = requests.post(url, json=payload)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print("✅ LOGIN BEM-SUCEDIDO!")
    print(f"Usuário: {data['data']['user']['nome']}")
    print(f"Token: {data['data']['access_token'][:50]}...")
else:
    print(f"Resposta: {response.text}")
