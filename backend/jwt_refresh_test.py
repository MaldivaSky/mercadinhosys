import requests
import time

BASE_URL = "http://localhost:5000/api"

def test_refresh_flow():
    # 1. Login
    print("Tentando login...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin_elite",
        "password": "adminElite123"
    })
    
    if login_res.status_code != 200:
        print(f"ERRO no login: {login_res.status_code} - {login_res.text}")
        return

    data = login_res.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    
    print("Login OK. Refresh token obtido.")
    
    # 2. Refresh
    print("Tentando refresh...")
    refresh_res = requests.post(
        f"{BASE_URL}/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    
    if refresh_res.status_code == 200:
        print("✅ Refresh SUCESSO!")
        print(refresh_res.json())
    else:
        print(f"❌ Refresh FALHOU: {refresh_res.status_code} - {refresh_res.text}")

if __name__ == "__main__":
    test_refresh_flow()
