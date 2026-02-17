
import requests
import json

def check_cloud_schema():
    base_url = "https://mercadinhosys.onrender.com/api"
    
    print(f"Tentando schema-check em {base_url}/auth/schema-check...")
    try:
        # Note: /api/auth/schema-check according to auth.py
        r = requests.get(f"{base_url}/auth/schema-check", timeout=15)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))

    except Exception as e:
        print(f"Erro na requisição: {e}")

if __name__ == "__main__":
    check_cloud_schema()
