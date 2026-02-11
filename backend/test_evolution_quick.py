import sys
sys.path.insert(0, '.')
from app import create_app
from app.dashboard_cientifico import DashboardOrchestrator

app = create_app()
with app.app_context():
    orch = DashboardOrchestrator(1)
    data = orch.get_scientific_dashboard(30)
    rh = data.get('rh', {})
    evo = rh.get('evolution_turnover', [])
    print(f'Evolution turnover tem {len(evo)} meses')
    for item in evo[:3]:
        print(f"{item['mes']}: adm={item.get('admissoes',0)}, dem={item.get('demissoes',0)}, aus={item.get('ausencias',0)}, atr={item.get('atrasos',0)}, he={item.get('horas_extras',0)}")
