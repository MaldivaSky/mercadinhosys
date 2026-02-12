
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_dashboard():
    # 1. Login
    print("Tentando login...")
    login_data = {
        "username": "admin",
        "senha": "123" 
    }
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"Erro no login: {response.text}")
            return

        data = response.json()
        token = data['data']['access_token']
        print("Login realizado com sucesso.")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        # CHAMADA 1
        print("\nChamada 1: (/api/dashboard/cientifico?days=30)...")
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/dashboard/cientifico?days=30", headers=headers)
        duration = time.time() - start_time
        print(f"Status 1: {response.status_code}")
        print(f"Tempo 1: {duration:.2f} segundos")

        # CHAMADA 2 (Deve ser instantânea agora)
        print("\nChamada 2 (Cache): (/api/dashboard/cientifico?days=30)...")
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/dashboard/cientifico?days=30", headers=headers)
        duration = time.time() - start_time
        print(f"Status 2: {response.status_code}")
        print(f"Tempo 2: {duration:.2f} segundos")
        
        if response.status_code == 200:
            res_data = response.json()
            # print(f"Chaves na raiz: {list(res_data.keys())}")
            dashboard_data = res_data.get('data', {})
            perf = dashboard_data.get('_performance', {})
            print(f"Tempo no servidor (da resposta): {perf.get('total_time', 'N/A')} segundos")
            
            produtos_estrela = dashboard_data.get('produtos_estrela', [])
            if produtos_estrela:
                print(f"Produto estrela: {produtos_estrela[0].get('nome')}")
                print(f"Última compra: {produtos_estrela[0].get('ultima_compra')}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    test_dashboard()
