import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app, db
from app.dashboard_cientifico.data_layer import DataLayer

app = create_app()

with app.app_context():
    print("--- Debugging Dashboard Logic ---")
    estabelecimento_id = 1
    days = 30
    
    end_date = datetime.utcnow()
    start_current = end_date - timedelta(days=days)
    
    print(f"Period: {start_current} to {end_date}")
    
    # 1. Test get_expense_details (The one likely returning [])
    print("\n[1] Testing get_expense_details...")
    expenses = DataLayer.get_expense_details(estabelecimento_id, start_current, end_date)
    print(f"Result count: {len(expenses)}")
    print(expenses)
    
    total_despesas = sum([float(exp.get("valor", 0)) for exp in expenses])
    print(f"Total Despesas Calculated: {total_despesas}")
    
    # 2. Test get_sales_financials
    print("\n[2] Testing get_sales_financials...")
    financials = DataLayer.get_sales_financials(estabelecimento_id, start_current, end_date)
    print(financials)
    
    revenue = float(financials.get("revenue", 0.0))
    gross_profit = float(financials.get("gross_profit", 0.0))
    
    net_profit = gross_profit - total_despesas
    print(f"\n[Calculated] Net Profit: {net_profit} (should be ~ -4344 if expenses match DRE)")
