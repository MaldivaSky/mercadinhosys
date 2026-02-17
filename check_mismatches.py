
import os
import sys
import re

# Adiciona o backend ao path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.models import db

def check_tablename_mismatches():
    # Tabelas na nuvem (obtidas no passo anterior)
    cloud_tables = [
        'alembic_version', 'banco_horas', 'beneficios', 'caixa', 
        'categorias_produto', 'clientes', 'configuracao_horario', 
        'configuracoes', 'despesas', 'estabelecimentos', 'fornecedores', 
        'funcionarios', 'funcionarios_beneficios', 'historico_precos', 
        'movimentacoes_estoque', 'pedidos_compra', 'pedidos_compra_itens', 
        'produtos', 'registro_ponto', 'venda_itens', 'vendas'
    ]
    
    mismatches = []
    
    # Inspeciona modelos carregados no metadata
    for table_name in db.metadata.tables.keys():
        if table_name not in cloud_tables:
            mismatches.append(f"Local table '{table_name}' NOT FOUND in cloud.")
            
    for ct in cloud_tables:
        if ct not in db.metadata.tables.keys():
            mismatches.append(f"Cloud table '{ct}' NOT FOUND in local models.")
            
    if not mismatches:
        print("SEM DISCREPÂNCIAS ENCONTRADAS!")
    else:
        print("--- DISCREPÂNCIAS ---")
        for m in mismatches:
            print(m)

if __name__ == "__main__":
    check_tablename_mismatches()
