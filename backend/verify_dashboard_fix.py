import sys
import os
from datetime import datetime

# Adicionar diretório pai ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.dashboard_cientifico.orchestration import DashboardOrchestrator

app = create_app()

def verify_dashboard():
    with app.app_context():
        # Obter o primeiro estabelecimento
        from app.models import Estabelecimento
        estab = Estabelecimento.query.first()
        if not estab:
            print("❌ Nenhum estabelecimento encontrado.")
            return

        print(f"🏢 Verificando Dashboard para: {estab.nome_fantasia} (ID: {estab.id})")
        
        orchestrator = DashboardOrchestrator(estab.id)
        
        # Testar para 30 dias
        data = orchestrator.get_scientific_dashboard(days=30)
        
        financials = data.get('financials', {})
        print("\n📊 DADOS FINANCEIROS CONSOLIDADOS (Backend):")
        print(f"Revenue (Faturamento): R$ {financials.get('revenue', 0):,.2f}")
        print(f"COGS (CMV):            R$ {financials.get('cogs', 0):,.2f}")
        print(f"Gross Profit (Bruto):  R$ {financials.get('gross_profit', 0):,.2f}")
        print(f"Expenses (Despesas):   R$ {financials.get('expenses', 0):,.2f}")
        print(f"Net Profit (Líquido):  R$ {financials.get('net_profit', 0):,.2f}")
        print(f"Net Margin:            {financials.get('net_margin', 0):.2f}%")
        print(f"ROI:                   {financials.get('roi', 0):.2f}%")
        
        print("\n🔍 VERIFICAÇÃO DE LÓGICA:")
        revenue = financials.get('revenue', 0)
        cogs = financials.get('cogs', 0)
        gross_profit = financials.get('gross_profit', 0)
        net_profit = financials.get('net_profit', 0)
        
        expected_gross = revenue - cogs
        print(f"Gross Profit matches (Revenue - COGS)? {'✅' if abs(gross_profit - expected_gross) < 0.01 else f'❌ (Diff: {gross_profit - expected_gross})'}")
        
        # O teste de Net Profit depende da subtracao de despesas.
        # Mas o importante é que COGS != Total Inventory
        inventory = data.get('inventory', {})
        total_inventory_value = inventory.get('valor_total', 0)
        print(f"\n📦 INVENTÁRIO (Ativo): R$ {total_inventory_value:,.2f}")
        
        if abs(cogs - total_inventory_value) < 0.01 and cogs > 0:
            print("⚠️ AVISO: COGS é igual ao Valor do Estoque Total. Isso indica que a correção pode não ter surtido efeito se o banco de dados tiver poucos dados ou se a lógica antiga persistir.")
        else:
            print("✅ COGS é diferente do Valor Total do Estoque. A correção parece ter funcionado.")

if __name__ == "__main__":
    verify_dashboard()
