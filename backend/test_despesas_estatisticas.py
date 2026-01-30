import requests
import json

# Login primeiro
login_response = requests.post(
    "http://localhost:5000/api/auth/login",
    json={"email": "admin@empresa.com", "senha": "admin123"}
)

if login_response.status_code == 200:
    data = login_response.json()
    token = data.get("access_token") or data.get("data", {}).get("access_token")
    print(f"✅ Login bem-sucedido! Token: {token[:50] if token else 'N/A'}...")
    print(f"Response completa: {json.dumps(data, indent=2)}")
    
    if not token:
        print("❌ Token não encontrado na resposta!")
        exit(1)
    
    # Testar estatísticas
    headers = {"Authorization": f"Bearer {token}"}
    stats_response = requests.get(
        "http://localhost:5000/api/despesas/estatisticas",
        headers=headers
    )
    
    print(f"\n📊 Status: {stats_response.status_code}")
    print(f"📊 Response:")
    print(json.dumps(stats_response.json(), indent=2, ensure_ascii=False))
else:
    print(f"❌ Erro no login: {login_response.status_code}")
    print(login_response.text)
