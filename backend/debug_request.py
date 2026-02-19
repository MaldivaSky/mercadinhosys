import requests
import json

try:
    print("Tentando acessar /api/configuracao/estabelecimento...")
    response = requests.get("http://localhost:5000/api/configuracao/estabelecimento")
    
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print("Response Text:")
        print(response.text)

except Exception as e:
    print(f"Erro ao conectar: {e}")
