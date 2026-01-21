#!/usr/bin/env python3
"""
Teste direto do dashboard científico
"""
from app import create_app
from app.dashboard_cientifico import DashboardOrchestrator

app = create_app()
with app.app_context():
    orchestrator = DashboardOrchestrator(1)
    try:
        data = orchestrator.get_scientific_dashboard()
        print('✅ Dashboard científico funcionando!')
        print(f'📊 Total vendas hoje: R$ {data["hoje"]["total_vendas"]:.2f}')
        print(f'📈 Curva ABC - Total produtos: {len(data["analise_produtos"]["curva_abc"]["produtos"])}')
        print(f'⭐ Produtos estrela: {len(data["analise_produtos"]["produtos_estrela"])}')
        print(f'🐌 Produtos lentos: {len(data["analise_produtos"]["produtos_lentos"])}')
        print(f'🔮 Previsão demanda: {len(data["analise_produtos"]["previsao_demanda"])}')

        # Verificar se há dados reais
        if data["analise_produtos"]["curva_abc"]["produtos"]:
            print(f'📊 Primeiro produto ABC: {data["analise_produtos"]["curva_abc"]["produtos"][0]["nome"]}')
        if data["analise_produtos"]["produtos_estrela"]:
            print(f'⭐ Primeiro produto estrela: {data["analise_produtos"]["produtos_estrela"][0]["nome"]}')

        # Verificar resumo ABC
        resumo = data["analise_produtos"]["curva_abc"]["resumo"]
        print(f'📊 Classe A: {resumo["A"]["quantidade"]} produtos ({resumo["A"]["percentual"]:.1f}%)')
        print(f'📊 Classe B: {resumo["B"]["quantidade"]} produtos ({resumo["B"]["percentual"]:.1f}%)')
        print(f'📊 Classe C: {resumo["C"]["quantidade"]} produtos ({resumo["C"]["percentual"]:.1f}%)')

    except Exception as e:
        print(f'❌ Erro no dashboard: {e}')
        import traceback
        traceback.print_exc()