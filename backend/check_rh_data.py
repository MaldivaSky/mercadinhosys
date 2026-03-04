
import os
import sys
from datetime import datetime, date

# Adiciona o diretório atual ao sys.path para importar o app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Estabelecimento, Funcionario, RegistroPonto, FuncionarioBeneficio
from app.dashboard_cientifico.data_layer import DataLayer

app = create_app()

with app.app_context():
    est = Estabelecimento.query.first()
    if not est:
        print("Erro: Nenhum estabelecimento encontrado!")
        sys.exit(1)
    
    id_int = est.id
    id_str = str(id_int)
    
    print(f"Testando get_rh_metrics com ID {id_int} (int)...")
    metrics_int = DataLayer.get_rh_metrics(id_int, 30)
    print(f"  Funcionários ativos: {metrics_int.get('funcionarios_ativos')}")
    print(f"  Total entradas: {metrics_int.get('total_entradas_periodo')}")
    print(f"  Custo folha: {metrics_int.get('custo_folha_estimado')}")
    
    print(f"\nTestando get_rh_metrics com ID '{id_str}' (str)...")
    try:
        metrics_str = DataLayer.get_rh_metrics(id_str, 30)
        print(f"  Funcionários ativos: {metrics_str.get('funcionarios_ativos')}")
        print(f"  Total entradas: {metrics_str.get('total_entradas_periodo')}")
        print(f"  Custo folha: {metrics_str.get('custo_folha_estimado')}")
    except Exception as e:
        print(f"  Erro ao testar com string: {e}")

    # Check for salary base
    f = Funcionario.query.filter_by(estabelecimento_id=id_int, ativo=True).first()
    if f:
        print(f"\nFuncionário {f.nome}: Salário {f.salario_base}, Ativo {f.ativo}")

    # Check RegistroPonto status
    rp = RegistroPonto.query.filter_by(estabelecimento_id=id_int).first()
    if rp:
        print(f"\nExemplo RegistroPonto: Tipo {rp.tipo_registro}, Status {rp.status}, Minutos {rp.minutos_atraso}")
