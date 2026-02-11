#!/usr/bin/env python
"""
Test script to verify what the dashboard endpoint is returning
"""

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Estabelecimento, Funcionario
from app.dashboard_cientifico import DashboardOrchestrator

app = create_app()

def test_dashboard_data():
    """Test what the dashboard is returning"""
    with app.app_context():
        print("\n" + "="*80)
        print("🧪 TESTE: VERIFICAR DADOS DO DASHBOARD")
        print("="*80)
        
        # Get test data
        estabelecimento = Estabelecimento.query.first()
        if not estabelecimento:
            print("❌ Nenhum estabelecimento encontrado.")
            return False
        
        print(f"✅ Estabelecimento: {estabelecimento.razao_social}")
        
        # Get dashboard data
        print("\n📊 Carregando dados do dashboard para 30 dias...")
        orchestrator = DashboardOrchestrator(estabelecimento.id)
        data = orchestrator.get_scientific_dashboard(days=30)
        
        # Print structure
        print("\n🔍 Estrutura de dados retornada:")
        print(f"  - success: {data.get('success')}")
        print(f"  - timestamp: {data.get('timestamp')}")
        print(f"  - period_days: {data.get('period_days')}")
        
        # Print summary
        print("\n📈 Summary:")
        summary = data.get('summary', {})
        print(f"  - revenue: {summary.get('revenue')}")
        print(f"  - growth: {summary.get('growth')}")
        print(f"  - avg_ticket: {summary.get('avg_ticket')}")
        print(f"  - unique_customers: {summary.get('unique_customers')}")
        
        # Print inventory
        print("\n📦 Inventory:")
        inventory = data.get('inventory', {})
        print(f"  - total_produtos: {inventory.get('total_produtos')}")
        print(f"  - valor_total: {inventory.get('valor_total')}")
        print(f"  - baixo_estoque: {inventory.get('baixo_estoque')}")
        
        # Print expenses
        print("\n💰 Expenses:")
        expenses = data.get('expenses', [])
        print(f"  - Total items: {len(expenses)}")
        if expenses:
            total_expenses = sum(e.get('total', e.get('valor', 0)) for e in expenses)
            print(f"  - Total value: {total_expenses}")
        
        # Print ABC
        print("\n📊 ABC Analysis:")
        abc = data.get('abc', {})
        print(f"  - Total produtos: {len(abc.get('produtos', []))}")
        resumo = abc.get('resumo', {})
        print(f"  - Classe A: {resumo.get('A', {}).get('quantidade', 0)} produtos")
        print(f"  - Classe B: {resumo.get('B', {}).get('quantidade', 0)} produtos")
        print(f"  - Classe C: {resumo.get('C', {}).get('quantidade', 0)} produtos")
        
        # Print produtos_estrela
        print("\n⭐ Produtos Estrela:")
        produtos_estrela = data.get('produtos_estrela', [])
        print(f"  - Total: {len(produtos_estrela)}")
        if produtos_estrela:
            for p in produtos_estrela[:3]:
                print(f"    - {p.get('nome')}: R$ {p.get('faturamento', 0):.2f}")
        
        # Print produtos_lentos
        print("\n🐢 Produtos Lentos:")
        produtos_lentos = data.get('produtos_lentos', [])
        print(f"  - Total: {len(produtos_lentos)}")
        if produtos_lentos:
            for p in produtos_lentos[:3]:
                print(f"    - {p.get('nome')}: {p.get('quantidade')} vendas, R$ {p.get('total_vendido', 0):.2f}")
        
        # Print timeseries
        print("\n📈 Timeseries:")
        timeseries = data.get('timeseries', [])
        print(f"  - Total dias: {len(timeseries)}")
        if timeseries:
            total_vendas = sum(t.get('total', 0) for t in timeseries)
            print(f"  - Total faturado: R$ {total_vendas:.2f}")
            print(f"  - Primeiro dia: {timeseries[0].get('data')} - R$ {timeseries[0].get('total', 0):.2f}")
            print(f"  - Último dia: {timeseries[-1].get('data')} - R$ {timeseries[-1].get('total', 0):.2f}")
        
        # Print RH metrics
        print("\n👥 RH Metrics:")
        rh = data.get('rh', {})
        print(f"  - total_beneficios_mensal: {rh.get('total_beneficios_mensal', 0)}")
        print(f"  - total_salarios: {rh.get('total_salarios', 0)}")
        print(f"  - funcionarios_ativos: {rh.get('funcionarios_ativos', 0)}")
        
        print("\n" + "="*80)
        print("✅ TESTE CONCLUÍDO")
        print("="*80 + "\n")
        
        return True

if __name__ == "__main__":
    success = test_dashboard_data()
    sys.exit(0 if success else 1)
