import requests
import json

# Fazer login primeiro
login_response = requests.post(
    'http://localhost:5000/api/auth/login',
    json={'username': 'admin', 'password': 'admin123'}
)

if login_response.status_code == 200:
    token = login_response.json()['data']['access_token']
    print(f"✅ Login OK, token: {token[:20]}...")
    
    # Buscar produtos
    headers = {'Authorization': f'Bearer {token}'}
    produtos_response = requests.get(
        'http://localhost:5000/api/produtos/estoque',
        headers=headers,
        params={'pagina': 1, 'por_pagina': 1, 'ativos': 'true'}
    )
    
    if produtos_response.status_code == 200:
        data = produtos_response.json()
        if data['produtos']:
            primeiro = data['produtos'][0]
            print("\n🔍 PRIMEIRO PRODUTO DA API:")
            print(json.dumps(primeiro, indent=2, ensure_ascii=False))
            
            # Verificar campos críticos
            print("\n📊 CAMPOS CRÍTICOS:")
            print(f"  quantidade_vendida: {primeiro.get('quantidade_vendida', 'AUSENTE')}")
            print(f"  total_vendido: {primeiro.get('total_vendido', 'AUSENTE')}")
            print(f"  ultima_venda: {primeiro.get('ultima_venda', 'AUSENTE')}")
        else:
            print("❌ Nenhum produto retornado")
    else:
        print(f"❌ Erro ao buscar produtos: {produtos_response.status_code}")
        print(produtos_response.text)
else:
    print(f"❌ Erro no login: {login_response.status_code}")
    print(login_response.text)
