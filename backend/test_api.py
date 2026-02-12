
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_produtos():
    # 1. Login
    print("Tentando login...")
    login_data = {
        "username": "admin",
        "senha": "123" 
    }
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        if response.status_code != 200:
            print(f"Erro no login: {response.text}")
            return

        data = response.json()
        token = data['data']['access_token']
        print("Login realizado com sucesso.")

        # 2. Listar produtos
        headers = {
            "Authorization": f"Bearer {token}"
        }
        print("\nTentando listar produtos...")
        response = requests.get(f"{BASE_URL}/produtos/", headers=headers)
        print(f"Listar produtos status: {response.status_code}")
        print(f"Resposta: {response.text[:500]}...")

        # 3. Testar sem barra no final
        print("\nTentando listar produtos (sem barra)...")
        response = requests.get(f"{BASE_URL}/produtos", headers=headers)
        print(f"Listar produtos (sem barra) status: {response.status_code}")
        print(f"Resposta: {response.text[:200]}...")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    test_produtos()
