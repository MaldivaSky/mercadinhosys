"""
Script para encontrar códigos de produtos duplicados no seed_test.py
"""

import re
from collections import Counter

# Ler o arquivo seed_test.py
with open('seed_test.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar todos os códigos de produtos no formato "XXX-###"
# Procurar por padrões como ("Nome", "Categoria", "COD-001", ...)
pattern = r'\("([^"]+)",\s*"([^"]+)",\s*"([A-Z]+-\d+)"'
matches = re.findall(pattern, content)

# Contar códigos
codes = [match[2] for match in matches]
code_counter = Counter(codes)

# Encontrar duplicados
duplicates = {code: count for code, count in code_counter.items() if count > 1}

print("=" * 60)
print("CÓDIGOS DUPLICADOS ENCONTRADOS:")
print("=" * 60)

if duplicates:
    for code, count in sorted(duplicates.items()):
        print(f"\n{code}: {count} ocorrências")
        # Mostrar onde cada código aparece
        for nome, categoria, cod in matches:
            if cod == code:
                print(f"  - {nome} ({categoria})")
else:
    print("✅ Nenhum código duplicado encontrado!")

print(f"\n\nTotal de produtos: {len(codes)}")
print(f"Códigos únicos: {len(set(codes))}")
print(f"Duplicados: {len(duplicates)}")
