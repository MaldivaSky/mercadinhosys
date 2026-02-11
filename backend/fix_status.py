#!/usr/bin/env python
"""Fix all 'concluida' status to 'finalizada' in data_layer.py"""

import os

file_path = "backend/app/dashboard_cientifico/data_layer.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences
content = content.replace("Venda.status == 'concluida'", "Venda.status == 'finalizada'")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed all 'concluida' to 'finalizada'")
