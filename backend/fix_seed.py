import os

filepath = 'seed_test.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_produto_block = [
    '                lote_str = f"L{NOW.strftime(\'%y%m\')}{random.randint(100, 999)}"\n',
    '                p = Produto(\n',
    '                    estabelecimento_id=ESTAB_ID,\n',
    '                    categoria_id=cat_map[cat],\n',
    '                    fornecedor_id=forn.id,\n',
    '                    nome=nome,\n',
    '                    codigo_barras=barcode,\n',
    '                    codigo_interno=interno,\n',
    '                    preco_custo=custo,\n',
    '                    preco_venda=venda,\n',
    '                    quantidade=qtd,\n',
    '                    quantidade_minima=qtd_min,\n',
    '                    unidade_medida=und,\n',
    '                    margem_lucro=margem,\n',
    '                    data_fabricacao=fabricacao,\n',
    '                    data_validade=validade,\n',
    '                    lote=lote_str,\n',
    '                    ativo=True,\n',
    '                    tipo=tipo,\n',
    '                    marca="Marca Genérica",\n',
    '                    fabricante="Fabricante Genérico",\n',
    '                    ncm="12345678",\n',
    '                    descricao=f"Produto {nome} - {tipo}",\n',
    '                    observacoes="Produto criado via seed",\n',
    '                    created_at=NOW - timedelta(days=random.randint(180, 360))\n'
]

# lines[:349] gets up to line 349 (0-indexed 348)
# lines[713:] gets line 714 onwards (0-indexed 713)
new_lines = lines[:349] + new_produto_block + lines[713:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Fixed {filepath}, old line count: {len(lines)}, new line count: {len(new_lines)}")
