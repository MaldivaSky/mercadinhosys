#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from app import create_app
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Criar token válido
    access_token = create_access_token(identity='1', additional_claims={
        'role': 'admin', 
        'status': 'ativo',
        'estabelecimento_id': 1
    })
    
    client = app.test_client()
    
    # Teste 1: Filtro por dias (padrão)
    print('Teste 1: Filtro por dias (30 dias)')
    response = client.get('/api/dashboard/cientifico?days=30', headers={'Authorization': f'Bearer {access_token}'})
    if response.status_code == 200:
        data = response.get_json()
        expenses = data.get('data', {}).get('expenses', [])
        total_exp = sum(e.get('total', 0) for e in expenses)
        print(f'  Status: OK')
        print(f'  Total despesas (30 dias): R$ {total_exp:,.2f}')
    else:
        print(f'  Erro: {response.status_code}')
    
    # Teste 2: Filtro por datas específicas (2 dias)
    print('\nTeste 2: Filtro por datas específicas (25/01 a 26/01)')
    start = '2025-01-25T00:00:00'
    end = '2025-01-26T23:59:59'
    response = client.get(f'/api/dashboard/cientifico?start_date={start}&end_date={end}', 
                         headers={'Authorization': f'Bearer {access_token}'})
    if response.status_code == 200:
        data = response.get_json()
        expenses = data.get('data', {}).get('expenses', [])
        total_exp = sum(e.get('total', 0) for e in expenses)
        sales = data.get('data', {}).get('summary', {}).get('revenue', {}).get('value', 0)
        print(f'  Status: OK')
        print(f'  Total despesas (2 dias): R$ {total_exp:,.2f}')
        print(f'  Total vendas (2 dias): R$ {sales:,.2f}')
        print(f'  Lucro (2 dias): R$ {sales - total_exp:,.2f}')
    else:
        print(f'  Erro: {response.status_code}')
        print(response.get_json())
