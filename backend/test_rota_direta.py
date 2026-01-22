import sys
sys.path.insert(0, '.')

from app import create_app
from flask import Flask
import json

app = create_app()

with app.test_client() as client:
    # Simular login para obter token
    login_response = client.post('/api/auth/login', 
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    if login_response.status_code == 200:
        data = json.loads(login_response.data)
        token = data['data']['access_token']
        print(f"✅ Token obtido: {token[:50]}...")
        
        # Testar rota de estoque
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/produtos/estoque?pagina=1&por_pagina=10', headers=headers)
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📊 Response: {response.data.decode()[:500]}")
        
        if response.status_code != 200:
            print(f"\n❌ ERRO: {response.data.decode()}")
    else:
        print(f"❌ Erro no login: {login_response.data.decode()}")
