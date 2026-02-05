#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import sys

# Execute seed_neon_rapido.py com input automático
process = subprocess.Popen(
    [sys.executable, 'seed_neon_rapido.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8'
)

# Enviar 's' automaticamente quando pedir confirmação
stdout, _ = process.communicate(input='s\n')

# Exibir output
print(stdout)
sys.exit(process.returncode)
