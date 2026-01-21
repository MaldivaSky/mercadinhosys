#!/usr/bin/env python3
"""
Script para testar todas as funções do data layer do dashboard científico
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.dashboard_cientifico.data_layer import DataLayer

def test_data_layer():
    app = create_app()
    with app.app_context():
        data_layer = DataLayer()

        print("🧪 Testando funções do Data Layer...")
        print("=" * 50)

        # Teste 1: get_top_products
        try:
            print("1. Testando get_top_products...")
            top_products = data_layer.get_top_products(estabelecimento_id=1, limit=10)
            print(f"   ✅ Sucesso: {len(top_products)} produtos retornados")
            if top_products:
                print(f"   📊 Top produto: {top_products[0]['nome']} - Qtd: {top_products[0]['quantidade_vendida']}")
        except Exception as e:
            print(f"   ❌ Erro em get_top_products: {e}")

        # Teste 2: analyze_inventory_abc
        try:
            print("\n2. Testando analyze_inventory_abc...")
            abc_data = data_layer.analyze_inventory_abc(estabelecimento_id=1)
            print(f"   ✅ Sucesso: {len(abc_data)} produtos analisados")
            if abc_data:
                print(f"   📊 Classe A: {len([p for p in abc_data if p['classe'] == 'A'])} produtos")
        except Exception as e:
            print(f"   ❌ Erro em analyze_inventory_abc: {e}")

        # Teste 3: get_slow_moving_products
        try:
            print("\n3. Testando get_slow_moving_products...")
            slow_products = data_layer.get_slow_moving_products(estabelecimento_id=1, days_threshold=30)
            print(f"   ✅ Sucesso: {len(slow_products)} produtos lentos encontrados")
            if slow_products:
                print(f"   📊 Produto mais lento: {slow_products[0]['nome']} - Última venda: {slow_products[0]['ultima_venda']}")
        except Exception as e:
            print(f"   ❌ Erro em get_slow_moving_products: {e}")

        # Teste 4: get_demand_forecast_data
        try:
            print("\n4. Testando get_demand_forecast_data...")
            forecast_data = data_layer.get_demand_forecast_data(estabelecimento_id=1, produto_id=1, days=30)
            print(f"   ✅ Sucesso: {len(forecast_data)} dias de dados retornados")
            if forecast_data:
                print(f"   📊 Primeiro dia: {forecast_data[0]['data']} - Vendas: {forecast_data[0]['vendas']}")
        except Exception as e:
            print(f"   ❌ Erro em get_demand_forecast_data: {e}")

        # Teste 5: get_temporal_analysis
        try:
            print("\n5. Testando get_temporal_analysis...")
            temporal_data = data_layer.get_temporal_analysis(estabelecimento_id=1, period='daily', days=30)
            print(f"   ✅ Sucesso: {len(temporal_data)} pontos temporais retornados")
            if temporal_data:
                print(f"   📊 Primeiro ponto: {temporal_data[0]['data']} - Vendas: {temporal_data[0]['total_vendas']}")
        except Exception as e:
            print(f"   ❌ Erro em get_temporal_analysis: {e}")

        print("\n" + "=" * 50)
        print("🏁 Testes concluídos!")

if __name__ == "__main__":
    test_data_layer()