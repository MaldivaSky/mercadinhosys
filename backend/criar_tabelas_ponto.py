"""
Script para criar tabelas do sistema de ponto
"""

from app import create_app
from app.models import db, RegistroPonto, ConfiguracaoHorario

app = create_app('development')

with app.app_context():
    print("Criando tabelas do sistema de ponto...")
    
    # Criar tabelas
    db.create_all()
    
    print("✅ Tabelas criadas com sucesso!")
    print("- registros_ponto")
    print("- configuracoes_horario")
