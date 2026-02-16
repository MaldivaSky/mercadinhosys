#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()
# Usar variável de ambiente — NUNCA coloque a URL com senha no código
neon_url = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not neon_url or not neon_url.startswith(("postgresql", "postgres")):
    print("❌ Configure AIVEN_DATABASE_URL ou DATABASE_URL no .env")
    sys.exit(1)
if neon_url.startswith("postgres://"):
    neon_url = neon_url.replace("postgres://", "postgresql://", 1)

print("Iniciando seed do Neon...")
print(f"Neon: ...@{neon_url.split('@')[-1].split('/')[0] if '@' in neon_url else '***'}")

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
