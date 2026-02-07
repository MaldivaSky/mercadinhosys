#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess

# Configurar NEON_DATABASE_URL
neon_url = "postgresql://neondb_owner:npg_jl8aMb4KGZBR@ep-quiet-smoke-a8z521gd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
os.environ['NEON_DATABASE_URL'] = neon_url

print("Iniciando seed do Neon...")
print(f"Neon: {neon_url[:50]}...")

# Executar seed com input 's'
process = subprocess.Popen(
    [sys.executable, 'seed_neon_rapido.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8'
)

stdout, _ = process.communicate(input='s\n')
lines = stdout.split('\n')

# Mostrar últimas 40 linhas
print('\n'.join(lines[-40:]))
