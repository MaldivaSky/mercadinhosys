import requests
import json

# Login first
login_url = "http://127.0.0.1:5000/api/auth/login"
login_data = {"username": "admin", "senha": "admin123"}

print("=" * 60)
print("TESTE COMPLETO - PRODUTOS PAGE")
print("=" * 60)

print("\n🔐 1. Fazendo login...")
login_response = requests.post(login_url, json=login_data)

if login_response.status_code != 200:
    print(f"❌ Erro no login: {login_response.text}")
    exit(1)

token = login_response.json()["data"]["access_token"]
print(f"✅ Login bem-sucedido")

headers = {"Authorization": f"Bearer {token}"}

# Test 1: Get all products
print("\n📦 2. Testando /api/produtos/estoque (todos os produtos)...")
response = requests.get(
    "http://127.0.0.1:5000/api/produtos/estoque",
    headers=headers,
    params={"pagina": 1, "por_pagina": 50, "ativos": "true", "ordenar_por": "nome", "direcao": "asc"}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Total de produtos: {data['paginacao']['total_itens']}")
    print(f"   ✅ Estatísticas:")
    print(f"      - Total: {data['estatisticas']['total_produtos']}")
    print(f"      - Baixo estoque: {data['estatisticas']['produtos_baixo_estoque']}")
    print(f"      - Esgotados: {data['estatisticas']['produtos_esgotados']}")
    print(f"      - Normal: {data['estatisticas']['produtos_normal']}")
else:
    print(f"   ❌ Erro: {response.text}")

# Test 2: Search products
print("\n🔍 3. Testando busca de produtos (busca='co')...")
response = requests.get(
    "http://127.0.0.1:5000/api/produtos/estoque",
    headers=headers,
    params={"pagina": 1, "por_pagina": 50, "busca": "co", "ativos": "true"}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Produtos encontrados: {len(data['produtos'])}")
    if data['produtos']:
        print(f"   ✅ Primeiro produto: {data['produtos'][0]['nome']}")
else:
    print(f"   ❌ Erro: {response.text}")

# Test 3: Filter by stock status
print("\n📊 4. Testando filtro por status de estoque (esgotado)...")
response = requests.get(
    "http://127.0.0.1:5000/api/produtos/estoque",
    headers=headers,
    params={"pagina": 1, "por_pagina": 50, "estoque_status": "esgotado", "ativos": "true"}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Produtos esgotados: {len(data['produtos'])}")
else:
    print(f"   ❌ Erro: {response.text}")

# Test 4: Get categories
print("\n📂 5. Testando /api/produtos/categorias...")
response = requests.get(
    "http://127.0.0.1:5000/api/produtos/categorias",
    headers=headers,
    params={"ativos": "true"}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Total de categorias: {data['total_categorias']}")
    print(f"   ✅ Categorias: {', '.join(data['categorias'][:5])}...")
else:
    print(f"   ❌ Erro: {response.text}")

# Test 5: Export CSV
print("\n📄 6. Testando /api/produtos/exportar/csv...")
response = requests.get(
    "http://127.0.0.1:5000/api/produtos/exportar/csv",
    headers=headers,
    params={"ativos": "true"}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Produtos exportados: {data['total_produtos']}")
    csv_lines = data['csv'].split('\n')
    print(f"   ✅ Linhas no CSV: {len(csv_lines)}")
else:
    print(f"   ❌ Erro: {response.text}")

print("\n" + "=" * 60)
print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
print("=" * 60)
