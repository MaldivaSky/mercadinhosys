import requests
import json

url = "http://localhost:5000/api/auth/login"
payload = {"username": "admin", "senha": "admin123", "estabelecimento_id": 4}

print("🔐 Testando login com estabelecimento_id correto...")
response = requests.post(url, json=payload)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print("✅ LOGIN BEM-SUCEDIDO!")
    print(f"Usuário: {data['data']['user']['nome']}")
    print(f"Token: {data['data']['access_token'][:50]}...")
    print(f"Token completo: {data['data']['access_token']}")
    print(f"Refresh token: {data['data']['refresh_token'][:50]}...")

    # Salvar o token para usar em outros testes
    access_token = data["data"]["access_token"]
    refresh_token = data["data"]["refresh_token"]

    # Vamos testar a rota de validação do token
    print("\n🔍 Testando validação do token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    validate_response = requests.get(
        "http://localhost:5000/api/auth/validate", headers=headers
    )

    print(f"Status da validação: {validate_response.status_code}")
    if validate_response.status_code == 200:
        validate_data = validate_response.json()
        print("✅ Token válido!")
        print(f"Usuário validado: {validate_data['data']['user']['nome']}")
    else:
        print("❌ Falha na validação do token")
        print(validate_response.text)

    # Testar refresh token
    print("\n🔄 Testando refresh token...")
    refresh_response = requests.post(
        "http://localhost:5000/api/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    print(f"Status do refresh: {refresh_response.status_code}")
    if refresh_response.status_code == 200:
        refresh_data = refresh_response.json()
        print("✅ Refresh token funcionou!")
        print(f"Novo access token: {refresh_data['access_token'][:50]}...")
    else:
        print("❌ Falha no refresh token")
        print(refresh_response.text)

else:
    print("❌ Falha no login")
    print(response.text)
