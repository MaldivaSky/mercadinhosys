"""
Teste do gráfico de evolução de RH aprimorado
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.dashboard_cientifico import DashboardOrchestrator

app = create_app()

with app.app_context():
    # Simular estabelecimento_id = 1
    estabelecimento_id = 1
    
    print("🔍 Testando geração de evolution_turnover aprimorado...")
    print("=" * 60)
    
    try:
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        dashboard_data = orchestrator.get_scientific_dashboard(days=30)
        
        if dashboard_data and 'rh' in dashboard_data:
            rh_data = dashboard_data['rh']
            
            if 'evolution_turnover' in rh_data:
                evolution = rh_data['evolution_turnover']
                print(f"\n✅ Evolution Turnover gerado com sucesso!")
                print(f"📊 Total de meses: {len(evolution)}")
                print("\n📈 Dados por mês:")
                print("-" * 60)
                
                for item in evolution:
                    print(f"\n📅 {item['mes']}")
                    print(f"   ➕ Admissões: {item['admissoes']}")
                    print(f"   ➖ Demissões: {item['demissoes']}")
                    print(f"   ❌ Ausências: {item.get('ausencias', 0)}")
                    print(f"   ⏰ Atrasos: {item.get('atrasos', 0)}")
                    print(f"   ⏱️  Horas Extras: {item.get('horas_extras', 0)}")
                
                print("\n" + "=" * 60)
                print("✅ Teste concluído com sucesso!")
                print("\n💡 O gráfico agora mostra 5 séries:")
                print("   1. Admissões (verde)")
                print("   2. Demissões (vermelho)")
                print("   3. Ausências (laranja)")
                print("   4. Atrasos (roxo)")
                print("   5. Horas Extras (ciano)")
                
            else:
                print("❌ Erro: evolution_turnover não encontrado nos dados de RH")
        else:
            print("❌ Erro: Dados de RH não encontrados")
            
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        import traceback
        traceback.print_exc()
