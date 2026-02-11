#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste COMPLETO do Dashboard - Verifica TODOS os gráficos e funcionalidades
"""
import sys
sys.path.insert(0, '.')
from app import create_app
from flask_jwt_extended import create_access_token
import json

app = create_app()
with app.app_context():
    access_token = create_access_token(identity='1', additional_claims={
        'role': 'admin', 
        'status': 'ativo',
        'estabelecimento_id': 1
    })
    
    client = app.test_client()
    response = client.get('/api/dashboard/cientifico?days=30', headers={'Authorization': f'Bearer {access_token}'})
    
    if response.status_code != 200:
        print(f'ERRO: Status {response.status_code}')
        print(response.get_json())
        sys.exit(1)
    
    data = response.get_json()['data']
    
    print('=' * 80)
    print('TESTE COMPLETO DO DASHBOARD')
    print('=' * 80)
    
    # 1. RESUMO EXECUTIVO
    print('\n1. RESUMO EXECUTIVO (Summary)')
    summary = data.get('summary', {})
    print(f'   Faturamento: R$ {summary.get("revenue", {}).get("value", 0):,.2f}')
    print(f'   Crescimento: {summary.get("growth", {}).get("value", 0):.1f}%')
    print(f'   Ticket Médio: R$ {summary.get("avg_ticket", {}).get("value", 0):,.2f}')
    print(f'   Clientes Únicos: {summary.get("unique_customers", 0)}')
    
    if not summary.get("revenue", {}).get("value"):
        print('   ⚠️ FATURAMENTO ZERADO!')
    
    # 2. TIMESERIES (Gráfico de Linha - Vendas por Dia)
    print('\n2. TIMESERIES (Gráfico de Linha - Vendas por Dia)')
    timeseries = data.get('timeseries', [])
    print(f'   Dias com dados: {len(timeseries)}')
    if timeseries:
        print(f'   Primeiro dia: {timeseries[0].get("data")} - R$ {timeseries[0].get("total", 0):,.2f}')
        print(f'   Último dia: {timeseries[-1].get("data")} - R$ {timeseries[-1].get("total", 0):,.2f}')
        total_ts = sum(d.get('total', 0) for d in timeseries)
        print(f'   Total período: R$ {total_ts:,.2f}')
    else:
        print('   ⚠️ SEM DADOS DE TIMESERIES!')
    
    # 3. FORECAST (Previsão)
    print('\n3. FORECAST (Previsão de Vendas)')
    forecast = data.get('forecast', [])
    print(f'   Dias previstos: {len(forecast)}')
    if forecast:
        print(f'   Primeira previsão: {forecast[0].get("dia")} - R$ {forecast[0].get("previsao", 0):,.2f}')
    else:
        print('   ⚠️ SEM DADOS DE FORECAST!')
    
    # 4. TREND (Tendência)
    print('\n4. TREND (Tendência de Vendas)')
    trend = data.get('trend', {})
    print(f'   Tendência: {trend.get("trend", "N/A")}')
    print(f'   Crescimento: {trend.get("growth_percent", 0):.1f}%')
    print(f'   Melhor dia: {trend.get("best_day", {}).get("day", "N/A")} - R$ {trend.get("best_day", {}).get("avg_sales", 0):,.2f}')
    print(f'   Pior dia: {trend.get("worst_day", {}).get("day", "N/A")} - R$ {trend.get("worst_day", {}).get("avg_sales", 0):,.2f}')
    
    # 5. INVENTORY (Estoque)
    print('\n5. INVENTORY (Estoque)')
    inventory = data.get('inventory', {})
    print(f'   Valor total: R$ {inventory.get("valor_total", 0):,.2f}')
    print(f'   Produtos baixo estoque: {inventory.get("baixo_estoque", 0)}')
    
    # 6. EXPENSES (Despesas)
    print('\n6. EXPENSES (Despesas por Categoria)')
    expenses = data.get('expenses', [])
    print(f'   Categorias: {len(expenses)}')
    total_exp = 0
    for exp in expenses[:5]:
        print(f'   - {exp.get("tipo", "N/A")}: R$ {exp.get("valor", 0):,.2f}')
        total_exp += exp.get('valor', 0)
    print(f'   Total despesas: R$ {total_exp:,.2f}')
    
    # 7. SALES BY HOUR (Vendas por Hora)
    print('\n7. SALES BY HOUR (Gráfico de Barras - Vendas por Hora)')
    sales_by_hour = data.get('sales_by_hour', [])
    print(f'   Horas com dados: {len(sales_by_hour)}')
    if sales_by_hour:
        for h in sales_by_hour[:3]:
            print(f'   {h.get("hora")}h: {h.get("qtd", 0)} vendas - R$ {h.get("total", 0):,.2f}')
    else:
        print('   ⚠️ SEM DADOS DE VENDAS POR HORA!')
    
    # 8. ABC ANALYSIS (Curva ABC)
    print('\n8. ABC ANALYSIS (Curva ABC - Pareto)')
    abc = data.get('abc', {})
    resumo = abc.get('resumo', {})
    print(f'   Classe A: {resumo.get("A", {}).get("quantidade", 0)} produtos - {resumo.get("A", {}).get("percentual", 0):.1f}% faturamento')
    print(f'   Classe B: {resumo.get("B", {}).get("quantidade", 0)} produtos - {resumo.get("B", {}).get("percentual", 0):.1f}% faturamento')
    print(f'   Classe C: {resumo.get("C", {}).get("quantidade", 0)} produtos - {resumo.get("C", {}).get("percentual", 0):.1f}% faturamento')
    
    # 9. PRODUTOS ESTRELA
    print('\n9. PRODUTOS ESTRELA (Top Produtos)')
    produtos_estrela = data.get('produtos_estrela', [])
    print(f'   Quantidade: {len(produtos_estrela)}')
    if produtos_estrela:
        for p in produtos_estrela[:3]:
            print(f'   - {p.get("nome", "N/A")}: R$ {p.get("total_vendido", 0):,.2f} (Margem: {p.get("margem", 0):.1f}%)')
    else:
        print('   ⚠️ SEM PRODUTOS ESTRELA!')
    
    # 10. PRODUTOS LENTOS
    print('\n10. PRODUTOS LENTOS (Produtos com Baixo Giro)')
    produtos_lentos = data.get('produtos_lentos', [])
    print(f'   Quantidade: {len(produtos_lentos)}')
    if produtos_lentos:
        for p in produtos_lentos[:3]:
            print(f'   - {p.get("nome", "N/A")}: {p.get("dias_estoque", 0)} dias em estoque')
    else:
        print('   ⚠️ SEM PRODUTOS LENTOS!')
    
    # 11. CORRELATIONS (Correlações)
    print('\n11. CORRELATIONS (Correlações Estatísticas)')
    correlations = data.get('correlations', [])
    print(f'   Quantidade: {len(correlations)}')
    if correlations:
        for c in correlations[:3]:
            print(f'   - {c.get("variavel1", "N/A")} vs {c.get("variavel2", "N/A")}: {c.get("correlacao", 0):.2f}')
    else:
        print('   ⚠️ SEM CORRELAÇÕES!')
    
    # 12. ANOMALIES (Anomalias)
    print('\n12. ANOMALIES (Anomalias Detectadas)')
    anomalies = data.get('anomalies', [])
    print(f'   Quantidade: {len(anomalies)}')
    if anomalies:
        for a in anomalies[:3]:
            print(f'   - {a.get("tipo", "N/A")}: {a.get("descricao", "N/A")}')
    else:
        print('   ⚠️ SEM ANOMALIAS DETECTADAS!')
    
    # 13. PERIOD ANALYSIS (Análise por Período)
    print('\n13. PERIOD ANALYSIS (Análise Manhã/Tarde/Noite)')
    period = data.get('period_analysis', {})
    for periodo, dados in period.items():
        print(f'   {periodo.upper()}: R$ {dados.get("faturamento", 0):,.2f} ({dados.get("vendas", 0)} vendas)')
    
    # 14. WEEKDAY ANALYSIS (Análise por Dia da Semana)
    print('\n14. WEEKDAY ANALYSIS (Análise por Dia da Semana)')
    weekday = data.get('weekday_analysis', {})
    for dia, dados in list(weekday.items())[:3]:
        print(f'   {dia}: R$ {dados.get("faturamento", 0):,.2f} ({dados.get("vendas", 0)} vendas)')
    
    # 15. PRODUCT HOURLY RECOMMENDATIONS
    print('\n15. PRODUCT HOURLY RECOMMENDATIONS (Recomendações de Estoque)')
    recs = data.get('product_hourly_recommendations', [])
    print(f'   Quantidade: {len(recs)}')
    if recs:
        for r in recs[:3]:
            print(f'   - {r.get("produto", "N/A")}: {r.get("quantidade_vendida", 0)} un/{r.get("periodo", "N/A").lower()}')
    else:
        print('   ⚠️ SEM RECOMENDAÇÕES!')
    
    # 16. RH METRICS
    print('\n16. RH METRICS (Recursos Humanos)')
    rh = data.get('rh', {})
    print(f'   Funcionários ativos: {rh.get("funcionarios_ativos", 0)}')
    print(f'   Custo folha estimado: R$ {rh.get("custo_folha_estimado", 0):,.2f}')
    print(f'   Taxa pontualidade: {rh.get("taxa_pontualidade", 0):.1f}%')
    
    # RESUMO FINAL
    print('\n' + '=' * 80)
    print('RESUMO DE PROBLEMAS ENCONTRADOS:')
    print('=' * 80)
    
    problemas = []
    
    if not summary.get("revenue", {}).get("value"):
        problemas.append('❌ Faturamento zerado')
    if not timeseries:
        problemas.append('❌ Sem dados de timeseries')
    if not forecast:
        problemas.append('❌ Sem dados de forecast')
    if not sales_by_hour:
        problemas.append('❌ Sem dados de vendas por hora')
    if not produtos_estrela:
        problemas.append('❌ Sem produtos estrela')
    if not produtos_lentos:
        problemas.append('❌ Sem produtos lentos')
    if not correlations:
        problemas.append('❌ Sem correlações')
    if not anomalies:
        problemas.append('❌ Sem anomalias')
    if not recs:
        problemas.append('❌ Sem recomendações de estoque')
    
    if problemas:
        for p in problemas:
            print(p)
    else:
        print('OK - TODOS OS DADOS PRESENTES E CORRETOS!')
    
    print('=' * 80)
