#!/usr/bin/env python
import sys
sys.path.insert(0, '.')
from app import create_app
from flask_jwt_extended import create_access_token
import json

app = create_app()
with app.app_context():
    # Criar token válido
    access_token = create_access_token(identity='1', additional_claims={
        'role': 'admin', 
        'status': 'ativo',
        'estabelecimento_id': 1
    })
    
    client = app.test_client()
    response = client.get('/api/dashboard/cientifico?days=30', headers={'Authorization': f'Bearer {access_token}'})
    
    if response.status_code == 200:
        data = response.get_json()
        correlations = data.get('data', {}).get('correlations', [])
        print(f'Correlacoes encontradas: {len(correlations)}')
        for corr in correlations[:5]:
            print(f'\n  - {corr.get("variavel1")} vs {corr.get("variavel2")}')
            print(f'    Correlacao: {corr.get("correlacao"):.2f}')
            print(f'    Insight: {corr.get("insight")}')
    else:
        print(f'Erro: {response.status_code}')
        print(response.get_json())
