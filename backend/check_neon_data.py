#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar se os dados foram replicados para Neon PostgreSQL
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Tentar obter URL do Neon de várias variáveis de ambiente
neon_url = (
    os.environ.get('NEON_DATABASE_URL') or 
    os.environ.get('DATABASE_URL_ORIG') or
    os.environ.get('NEON_DB_URL') or
    os.environ.get('DB_PRIMARY') or
    os.environ.get('DATABASE_URL_TARGET') or
    os.environ.get('DATABASE_URL')
)

if not neon_url:
    print("❌ Nenhuma URL de banco de dados configurada!")
    sys.exit(1)

# Converter postgres:// para postgresql://
if neon_url.startswith("postgres://"):
    neon_url = neon_url.replace("postgres://", "postgresql://", 1)

print(f"🔍 Verificando banco Neon...")

try:
    engine = create_engine(neon_url)
    
    # Testar conexão
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Conexão com Neon estabelecida")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Verificar registros de ponto
    result = session.execute(text("SELECT COUNT(*) as total FROM registros_ponto"))
    ponto_count = result.scalar() or 0
    print(f"📍 Registros de ponto (RegistroPonto): {ponto_count}")
    
    # Verificar configurações de horário
    result = session.execute(text("SELECT COUNT(*) as total FROM configuracoes_horario"))
    config_count = result.scalar() or 0
    print(f"⏰ Configurações de horário (ConfiguracaoHorario): {config_count}")
    
    # Verificar funcionários
    result = session.execute(text("SELECT COUNT(*) as total FROM funcionarios"))
    func_count = result.scalar() or 0
    print(f"👥 Funcionários: {func_count}")
    
    # Verificar dados de hoje
    from datetime import date
    hoje = date.today()
    result = session.execute(text(f"SELECT COUNT(*) as total FROM registros_ponto WHERE data = '{hoje}'"))
    hoje_count = result.scalar() or 0
    print(f"📅 Registros de ponto de hoje ({hoje}): {hoje_count}")
    
    # Status geral
    print("\n" + "="*50)
    if ponto_count > 0 and config_count > 0:
        print("✅ TUDO OK! Dados foram replicados para Neon")
    else:
        print("⚠️  Dados incompletos:")
        if ponto_count == 0:
            print("  - RegistroPonto vazio")
        if config_count == 0:
            print("  - ConfiguracaoHorario vazio")
    
    session.close()
    
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
