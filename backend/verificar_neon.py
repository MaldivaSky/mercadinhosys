#!/usr/bin/env python3
"""
Script para verificar e popular banco Neon
Uso: python verificar_neon.py
"""

import os
import sys
from app import create_app, db
from app.models import Funcionario, Estabelecimento
from werkzeug.security import generate_password_hash

# Configurar DATABASE_URL para Neon
NEON_URL = "postgresql://neondb_owner:npg_jl8aMb4KGZBR@ep-quiet-smoke-a8z521gd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
os.environ['DATABASE_URL'] = NEON_URL
os.environ['FLASK_ENV'] = 'production'

def verificar_conexao():
    """Verifica se consegue conectar ao Neon"""
    print("🔍 Verificando conexão com Neon...")
    try:
        app = create_app('production')
        with app.app_context():
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1"))
            print("✅ Conexão com Neon OK!")
            return app
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)

def verificar_tabelas(app):
    """Verifica se as tabelas existem"""
    print("\n🔍 Verificando tabelas...")
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        
        tabelas_necessarias = ['funcionarios', 'estabelecimentos', 'produtos', 'clientes', 'vendas']
        tabelas_faltando = [t for t in tabelas_necessarias if t not in tabelas]
        
        if tabelas_faltando:
            print(f"⚠️ Tabelas faltando: {', '.join(tabelas_faltando)}")
            print("Execute: python seed_neon.py")
            return False
        else:
            print(f"✅ Todas as tabelas existem ({len(tabelas)} tabelas)")
            return True

def verificar_funcionarios(app):
    """Verifica funcionários no banco"""
    print("\n🔍 Verificando funcionários...")
    with app.app_context():
        funcionarios = Funcionario.query.all()
        
        if not funcionarios:
            print("❌ Nenhum funcionário encontrado!")
            return False
        
        print(f"✅ {len(funcionarios)} funcionário(s) encontrado(s):")
        for f in funcionarios:
            print(f"  • ID: {f.id} | Nome: {f.nome} | Email: {f.email} | Role: {f.role} | Status: {f.status}")
        
        return True

def criar_admin(app):
    """Cria usuário admin padrão"""
    print("\n🔧 Criando usuário admin...")
    with app.app_context():
        # Verificar se já existe
        admin_existente = Funcionario.query.filter_by(email='admin@mercadinho.com').first()
        if admin_existente:
            print(f"⚠️ Admin já existe (ID: {admin_existente.id})")
            return admin_existente.id
        
        # Verificar/criar estabelecimento
        estabelecimento = Estabelecimento.query.first()
        if not estabelecimento:
            print("  Criando estabelecimento...")
            estabelecimento = Estabelecimento(
                nome='Mercadinho Sys',
                cnpj='00000000000000',
                telefone='(00) 0000-0000',
                email='contato@mercadinho.com'
            )
            db.session.add(estabelecimento)
            db.session.flush()
        
        # Criar admin
        admin = Funcionario(
            nome='Admin',
            email='admin@mercadinho.com',
            senha=generate_password_hash('admin123'),
            role='ADMIN',
            status='ativo',
            estabelecimento_id=estabelecimento.id,
            permissoes={
                'pode_dar_desconto': True,
                'limite_desconto': 100,
                'pode_cancelar_venda': True,
                'pode_editar_produtos': True,
                'pode_ver_relatorios': True
            }
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Admin criado com sucesso!")
        print(f"  • ID: {admin.id}")
        print(f"  • Email: admin@mercadinho.com")
        print(f"  • Senha: admin123")
        
        return admin.id

def main():
    print("="*60)
    print("🔍 VERIFICADOR DE BANCO NEON")
    print("="*60)
    
    # 1. Verificar conexão
    app = verificar_conexao()
    
    # 2. Verificar tabelas
    tabelas_ok = verificar_tabelas(app)
    
    if not tabelas_ok:
        print("\n❌ Execute primeiro: python seed_neon.py")
        sys.exit(1)
    
    # 3. Verificar funcionários
    funcionarios_ok = verificar_funcionarios(app)
    
    # 4. Criar admin se necessário
    if not funcionarios_ok:
        print("\n🔧 Nenhum funcionário encontrado. Criando admin...")
        admin_id = criar_admin(app)
        print(f"\n✅ Admin criado com ID: {admin_id}")
    
    print("\n" + "="*60)
    print("✅ VERIFICAÇÃO CONCLUÍDA!")
    print("="*60)
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Acesse: https://mercadinhosys.vercel.app")
    print("2. Faça logout (limpe localStorage)")
    print("3. Faça login com:")
    print("   • Email: admin@mercadinho.com")
    print("   • Senha: admin123")
    print("4. Teste o PDV")
    print("\n")

if __name__ == '__main__':
    main()
