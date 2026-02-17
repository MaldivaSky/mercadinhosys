
import requests
import json

def get_error_details():
    base_url = "https://mercadinhosys.onrender.com/api"
    
    # Login para obter token
    print(f"Fazendo login em {base_url}/auth/login...")
    try:
        r = requests.post(f"{base_url}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=15)
        
        if r.status_code != 200:
            print(f"Falha no login: {r.status_code}")
            print(r.text)
            return
            
        data = r.json()
        token = data.get("data", {}).get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("Login OK! Iniciando testes...")

        # Teste 1: Ordenação com typo (esperado erro 500 se o backend for frágil)
        print(f"\n--- TESTE 1: Ordenação com TYPO (precocusto) ---")
        r1 = requests.get(f"{base_url}/produtos?ordenar_por=precocusto", headers=headers, timeout=15)
        print(f"Status: {r1.status_code}")
        if r1.status_code == 500:
            print(f"Erro capturado como esperado: {r1.text[:200]}")
        
        # Teste 2: Ordenação CORRETA (preco_custo)
        print(f"\n--- TESTE 2: Ordenação CORRETA (preco_custo) ---")
        r2 = requests.get(f"{base_url}/produtos?ordenar_por=preco_custo", headers=headers, timeout=15)
        print(f"Status: {r2.status_code}")
        if r2.status_code != 200:
            print(f"ERRO REAL: {r2.text[:200]}")
        else:
            print("Sucesso!")

        # Teste 3: Sem ordenação (Padrão)
        print(f"\n--- TESTE 3: Sem ordenação (Padrão) ---")
        r3 = requests.get(f"{base_url}/produtos", headers=headers, timeout=15)
        print(f"Status: {r3.status_code}")
        if r3.status_code != 200:
            print(f"ERRO REAL: {r3.text[:200]}")
        else:
            print("Sucesso!")

    except Exception as e:
        print(f"Erro na requisição: {e}")

if __name__ == "__main__":
    get_error_details()
