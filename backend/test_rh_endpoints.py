
import os
import sys
import json
from datetime import datetime

# Adiciona o diretório atual ao sys.path para importar o app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # Simulando um token para o estabelecimento 1
    additional_claims = {
        "estabelecimento_id": 1,
        "role": "ADMIN"
    }
    access_token = create_access_token(identity="1", additional_claims=additional_claims)
    
    client = app.test_client()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print("Testando /api/dashboard/rh/ponto/historico...")
    response = client.get("/api/dashboard/rh/ponto/historico", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        items = data.get("data", {}).get("items", [])
        print(f"Total de itens retornados: {len(items)}")
        if items:
            print(f"Exemplo do primeiro item: {json.dumps(items[0], indent=2)}")
    else:
        print(f"Erro: {response.get_data(as_text=True)}")

    print("\nTestando /api/rh/dashboard...")
    response = client.get("/api/rh/dashboard?days=30", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"Data keys: {data.get('data', {}).keys()}")
        rh_metrics = data.get("data", {})
        print(f"Funcionários ativos: {rh_metrics.get('funcionarios_ativos')}")
        print(f"Total atrasos: {rh_metrics.get('total_atrasos_qtd')}")
    else:
        print(f"Erro: {response.get_data(as_text=True)}")
