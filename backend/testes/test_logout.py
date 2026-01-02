import requests
import json


# Novo login para pegar tokens frescos
login_response = requests.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "admin", "senha": "admin123", "estabelecimento_id": 4},
)

if login_response.status_code == 200:
    tokens = login_response.json()["data"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    print("🔄 Testando refresh token...")
    refresh_response = requests.post(
        "http://localhost:5000/api/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    print(f"Status: {refresh_response.status_code}")
    if refresh_response.status_code == 200:
        new_token = refresh_response.json()["access_token"]
        print("✅ Refresh token funcionou!")
        print(f"Novo access token: {new_token[:50]}...")
    else:
        print("❌ Refresh token falhou")
        print(refresh_response.json())

print("\n🚪 Testando logout...")
logout_response = requests.post(
    "http://localhost:5000/api/auth/logout",
    headers={"Authorization": f"Bearer {access_token}"},
)

print(f"Status: {logout_response.status_code}")
if logout_response.status_code == 200:
    print("✅ Logout realizado com sucesso")
    print(logout_response.json())
else:
    print("❌ Logout falhou")
    print(logout_response.json())
