import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app
from app.dashboard_cientifico.orchestration import DashboardOrchestrator

app = create_app()

with app.app_context():
    print("--- Debugging Orchestrator ---")
    est_id = 1
    orch = DashboardOrchestrator(est_id)
    
    # Run logic
    print("Running get_scientific_dashboard...")
    result = orch._get_scientific_dashboard_logic(days=30)
    
    print("\n--- Financials Section ---")
    fin = result.get('summary', {})
    
    revenue = fin.get('revenue', 0)
    gross = fin.get('gross_profit', 0)
    net = fin.get('net_profit', 0)
    expenses = fin.get('expenses', 0)
    
    print(f"Revenue: {revenue}")
    print(f"Gross Profit: {gross}")
    print(f"Expenses: {expenses}")
    print(f"Net Profit: {net}")
    
    print("\n--- Consistency Check ---")
    if abs(net - (gross - expenses)) < 0.01:
        print("✅ Math OK: Net = Gross - Expenses")
    else:
        print(f"❌ Math FAIL: {net} != {gross} - {expenses}")

    if abs(net - gross) < 0.01 and expenses == 0:
        print("❌ ALARM: Net == Gross (Expenses are 0!)")
        
    print("\n--- Expense Details Source ---")
    exp_details = result.get('expenses', [])
    print(f"Expense Items Count: {len(exp_details)}")
    print(json.dumps(exp_details, default=str, indent=2))
