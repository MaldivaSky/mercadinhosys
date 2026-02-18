import csv
import io
import os
import sys
from decimal import Decimal

# Simular ambiente de teste sem precisar rodar o servidor Flask completo
# Vamos testar a logica de parsing em um script separado

def simulate_import(csv_content, delimiter=';'):
    stream = io.StringIO(csv_content)
    reader = csv.DictReader(stream, delimiter=delimiter)
    
    # Se nao encontrar nada com ';', tentar ','
    if not reader.fieldnames or len(reader.fieldnames) < 2:
        stream.seek(0)
        reader = csv.DictReader(stream, delimiter=',')
        
    print(f"Campos encontrados: {reader.fieldnames}")
    
    results = []
    for row_idx, row in enumerate(reader, start=1):
        try:
            nome = row.get('nome', '').strip()
            cat_nome = row.get('categoria', '').strip()
            preco_custo = row.get('preco_custo', '0').replace(',', '.')
            preco_venda = row.get('preco_venda', '0').replace(',', '.')
            
            if not nome or not cat_nome:
                print(f"Erro na linha {row_idx}: Campos obrigatorios ausentes")
                continue
                
            results.append({
                "nome": nome,
                "categoria": cat_nome,
                "custo": Decimal(preco_custo),
                "venda": Decimal(preco_venda)
            })
            print(f"Sucesso na linha {row_idx}: {nome}")
        except Exception as e:
            print(f"Erro na linha {row_idx}: {str(e)}")
            
    return results

# Teste 1: Padrão PT-BR (;)
test_csv_pt = """nome;categoria;preco_custo;preco_venda
Produto A;Cat 1;10,50;15,90
Produto B;Cat 2;5.00;7.50"""

print("--- Testando CSV PT-BR (;) ---")
simulate_import(test_csv_pt)

# Teste 2: Padrão US (,)
test_csv_us = """nome,categoria,preco_custo,preco_venda
Produto C,Cat 3,20.00,30.00
Produto D,Cat 1,1.50,2.50"""

print("\n--- Testando CSV US (,) ---")
simulate_import(test_csv_us)
