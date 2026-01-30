import requests
import json
from datetime import datetime, timedelta

# Login
login_response = requests.post(
    "http://localhost:5000/api/auth/login",
    json={"email": "admin@empresa.com", "senha": "admin123"}
)

if login_response.status_code == 200:
    data = login_response.json()
    token = data.get("access_token") or data.get("data", {}).get("access_token")
    print("Login bem-sucedido!")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Teste 1: Sem filtros
    print("\n" + "="*60)
    print("TESTE 1: Listar todas as despesas (sem filtros)")
    print("="*60)
    response = requests.get("http://localhost:5000/api/despesas", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total de despesas: {len(data.get('data', []))}")
        print(f"Primeira despesa: {data['data'][0]['descricao'] if data.get('data') else 'Nenhuma'}")
    
    # Teste 2: Filtro por categoria
    print("\n" + "="*60)
    print("TESTE 2: Filtrar por categoria 'Aluguel'")
    print("="*60)
    response = requests.get(
        "http://localhost:5000/api/despesas",
        headers=headers,
        params={"categoria": "Aluguel"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Despesas encontradas: {len(data.get('data', []))}")
        for d in data.get('data', [])[:3]:
            print(f"  - {d['descricao']} | {d['categoria']} | R$ {d['valor']}")
    
    # Teste 3: Filtro por tipo
    print("\n" + "="*60)
    print("TESTE 3: Filtrar por tipo 'fixa'")
    print("="*60)
    response = requests.get(
        "http://localhost:5000/api/despesas",
        headers=headers,
        params={"tipo": "fixa"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Despesas encontradas: {len(data.get('data', []))}")
        for d in data.get('data', [])[:3]:
            print(f"  - {d['descricao']} | Tipo: {d['tipo']} | R$ {d['valor']}")
    
    # Teste 4: Filtro por data
    print("\n" + "="*60)
    print("TESTE 4: Filtrar por período (últimos 30 dias)")
    print("="*60)
    hoje = datetime.now().date()
    inicio = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
    fim = hoje.strftime("%Y-%m-%d")
    response = requests.get(
        "http://localhost:5000/api/despesas",
        headers=headers,
        params={"inicio": inicio, "fim": fim}
    )
    print(f"Status: {response.status_code}")
    print(f"Período: {inicio} até {fim}")
    if response.status_code == 200:
        data = response.json()
        print(f"Despesas encontradas: {len(data.get('data', []))}")
        for d in data.get('data', [])[:3]:
            print(f"  - {d['descricao']} | Data: {d['data_despesa']} | R$ {d['valor']}")
    
    # Teste 5: Busca por texto
    print("\n" + "="*60)
    print("TESTE 5: Buscar por 'energia'")
    print("="*60)
    response = requests.get(
        "http://localhost:5000/api/despesas",
        headers=headers,
        params={"busca": "energia"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Despesas encontradas: {len(data.get('data', []))}")
        for d in data.get('data', [])[:3]:
            print(f"  - {d['descricao']} | {d['categoria']} | R$ {d['valor']}")
    
    # Teste 6: Filtro por recorrente
    print("\n" + "="*60)
    print("TESTE 6: Filtrar despesas recorrentes")
    print("="*60)
    response = requests.get(
        "http://localhost:5000/api/despesas",
        headers=headers,
        params={"recorrente": "true"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Despesas encontradas: {len(data.get('data', []))}")
        for d in data.get('data', [])[:3]:
            print(f"  - {d['descricao']} | Recorrente: {d['recorrente']} | R$ {d['valor']}")
    
    print("\n" + "="*60)
    print("TODOS OS TESTES CONCLUIDOS!")
    print("="*60)
else:
    print(f"Erro no login: {login_response.status_code}")
    print(login_response.text)
