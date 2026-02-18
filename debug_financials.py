import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app, db
from app.dashboard_cientifico.data_layer import DataLayer

app = create_app()

with app.app_context():
    print("--- Starting Debug ---")
    try:
        # Simulate the request parameters
        # User url: data_inicio=2026-01-19&data_fim=2026-02-18
        start_date = datetime(2026, 1, 19)
        end_date = datetime(2026, 2, 18)
        estabelecimento_id = 1 # Assuming ID 1 exists, or we can query one

        print(f"Testing for Estabelecimento: {estabelecimento_id}")
        print(f"Period: {start_date} to {end_date}")

        result = DataLayer.get_consolidated_financial_summary(estabelecimento_id, start_date, end_date)
        
        if result is None:
            print("❌ FAILURE: Method returned None (Exception was caught inside)")
            # Simulate what despesas.py does
            print("Simulating 500 response from despesas.py")
        else:
            print("✅ SUCCESS: Data retrieved")
            print("Keys:", result.keys())
            
            # Simulate despesas.py logic exactly
            cp = result['contas_pagar']
            vendas = result['vendas']
            desp = result['despesas']
            
            receita_bruta = vendas.get("revenue", 0.0)
            print(f"Receita Bruta: {receita_bruta}")
            
            total_pagar_aberto = cp['total_aberto']
            print(f"Total a Pagar Aberto: {total_pagar_aberto}")
            
            # Calculations
            indice_comprometimento = (total_pagar_aberto / receita_bruta * 100) if receita_bruta > 0 else 0
            print(f"Indice Comprometimento: {indice_comprometimento}")

            # Check for keys used in alerts
            print(f"Qtd Vencidos: {cp.get('qtd_vencidos')}")
            print(f"Total Vencido: {cp.get('total_vencido')}")
            
            # Check Cash Flow keys
            entradas_reais = vendas.get("total_recebido", 0.0)
            print(f"Entradas Reais: {entradas_reais}")
            
            saidas_reais = cp['pago_periodo'] + desp['total']
            print(f"Saidas Reais: {saidas_reais}")
            
            # Simulate jsonify payload construction to check for serialization errors
            payload = {
                 "dre_consolidado": {
                    "receita_bruta": vendas.get("revenue", 0.0),
                    "custo_mercadoria": vendas.get("cogs", 0.0),
                    "lucro_bruto": vendas.get("gross_profit", 0.0),
                    "despesas_operacionais": desp['total'],
                    "lucro_liquido": vendas.get("gross_profit", 0.0) - desp['total']
                }
            }
            import json
            print("Attempting serialization...")
            json.dumps(payload, default=str)
            print("✅ Serialization Successful")


    except Exception as e:
        print(f"❌ CRITICAL FAILURE (Uncaught): {e}")
        import  traceback
        traceback.print_exc()
