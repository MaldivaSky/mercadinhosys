#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
        
        print('Analises Temporais Retornadas:')
        print(f'  - period_analysis: {bool(data.get("data", {}).get("period_analysis"))}')
        print(f'  - weekday_analysis: {bool(data.get("data", {}).get("weekday_analysis"))}')
        print(f'  - product_hourly_recommendations: {len(data.get("data", {}).get("product_hourly_recommendations", []))} recomendacoes')
        print(f'  - hourly_sales_by_category: {bool(data.get("data", {}).get("hourly_sales_by_category"))}')
        
        # Mostrar período analysis
        period = data.get('data', {}).get('period_analysis', {})
        if period:
            print('\nAnalise por Periodo:')
            for periodo, dados in period.items():
                print(f'  {periodo.upper()}: R$ {dados.get("faturamento", 0):,.0f} ({dados.get("vendas", 0)} vendas)')
        
        # Mostrar weekday analysis
        weekday = data.get('data', {}).get('weekday_analysis', {})
        if weekday:
            print('\nAnalise por Dia da Semana:')
            for dia, dados in list(weekday.items())[:3]:
                print(f'  {dia}: R$ {dados.get("faturamento", 0):,.0f} ({dados.get("vendas", 0)} vendas)')
        
        # Mostrar recomendações
        recs = data.get('data', {}).get('product_hourly_recommendations', [])
        if recs:
            print('\nTop 3 Recomendacoes de Estoque:')
            for rec in recs[:3]:
                print(f'  - {rec.get("produto")} ({rec.get("categoria")}): {rec.get("quantidade_vendida")} un/dia no {rec.get("periodo").lower()}')
    else:
        print(f'Erro: {response.status_code}')
        print(response.get_json())
