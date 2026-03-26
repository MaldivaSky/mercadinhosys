#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_super_admin.py – SEED ROBUSTA PARA PAINEL SUPER ADMIN (SaaS)
==============================================================
Focado em:
1. Leads (Funil de Vendas)
2. Estabelecimentos (Tenants) em diversos estados (Plano, Status, Vencimento)
3. Configurações Globais
4. Super Admin (Dono do Sistema)
"""

import sys
import os
import random
from datetime import datetime, date, timedelta
from faker import Faker

# Ajuste de path para reconhecer o pacote 'app'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

fake = Faker('pt_BR')

from app import create_app
from app.models import (
    db, Estabelecimento, Funcionario, Lead, Configuracao, 
    ConfiguracaoHorario, Caixa, CategoriaProduto
)

def seed_super_admin(app=None):
    if not app:
        app = create_app('development')
    
    # Se já estamos em um context (como no seed_simulation_master), não precisamos do 'with'
    # mas para segurança, vamos usar um try/except para garantir que o db.session esteja ativo
    
    def internal_seed():
        print("[START] SEEDING SUPER ADMIN PANEL DATA...")

        # 1. Limpeza Seletiva (Opcional, mas vamos garantir o Super Admin)
        # db.drop_all() # Cuidado: se o usuário quiser manter os dados da seed_main, não damos drop_all
        # Mas o usuário pediu uma seed_main mais robusta, então vamos assumir reset de dados críticos.
        
        # 2. Criar Estabelecimento HQ (Sistema)
        print("--- Criando HQ e Super Admin...")
        hq = Estabelecimento.query.filter_by(cnpj="00000000000100").first()
        if not hq:
            hq = Estabelecimento(
                nome_fantasia="MercadinhoSys HQ",
                razao_social="MercadinhoSys SaaS Technology LTDA",
                cnpj="00000000000100",
                email="superadmin@mercadinhosys.com",
                telefone="(92) 99999-0000",
                cep="69000-000", logradouro="Alameda SaaS", numero="10", bairro="Distrito", cidade="Manaus", estado="AM",
                data_abertura=date(2023, 1, 1), plano="SaaS Master", plano_status="ativo"
            )
            db.session.add(hq)
            db.session.flush()

        # 3. Super Admin Oficial
        sa_email = "rafaelmaldivas@gmail.com"
        sa = Funcionario.query.filter_by(email=sa_email).first()
        if not sa:
            sa = Funcionario(
                estabelecimento_id=hq.id,
                nome="Rafael Maldivas (SaaS Owner)",
                username="maldivas",
                email=sa_email,
                cargo="PROPRIETÁRIO DO SISTEMA",
                role="ADMIN", # No backend is_super_admin checa role e email
                is_super_admin=True,
                status="ativo",
                cpf="34372131801", # CPF REAL DO USER (Rafael)
                data_nascimento=date(1985, 5, 20),
                celular="(92) 99123-4444",
                data_admissao=date(2023, 1, 1),
                cep="69000-000", logradouro="Residência HQ", numero="1", bairro="Ponta Negra", cidade="Manaus", estado="AM"
            )
            sa.set_senha("Mald1v@$")
            db.session.add(sa)
            db.session.commit()
            print(f"--- Super Admin criado: {sa_email}")

        # 4. Massa de Leads (Para o Funil de Vendas)
        print("--- Gerando Leads (Funil SaaS)...")
        origens = ["landing_page", "facebook", "google_ads", "indicacao", "panfletagem"]
        observacoes = [
            "Interessado no plano experimental",
            "Quer migrar do sistema concorrente X",
            "Abriu novo mercadinho no bairro Y",
            "Dúvidas sobre faturamento de nota fiscal",
            "Agendou demonstração"
        ]
        
        for _ in range(50):
            lead = Lead(
                nome=fake.name(),
                email=fake.email(),
                whatsapp=fake.phone_number()[:30],
                origem=random.choice(origens),
                observacao=random.choice(observacoes),
                data_cadastro=datetime.utcnow() - timedelta(days=random.randint(0, 60))
            )
            db.session.add(lead)
        
        print(f"--- 50 Leads criados.")

        # 5. Massa de Estabelecimentos (Tenants)
        print("--- Gerando Múltiplos Tenants em diferentes estados...")
        planos = ["Basic", "Experimental", "Advanced", "Premium"]
        status_list = ["ativo", "atrasado", "cancelado", "experimental"]
        
        for i in range(15):
            nome = fake.company()
            p = random.choice(planos)
            s = random.choice(status_list)
            venc = None
            if s == "ativo":
                venc = datetime.utcnow() + timedelta(days=random.randint(5, 30))
            elif s == "atrasado":
                venc = datetime.utcnow() - timedelta(days=random.randint(1, 15))
            
            est = Estabelecimento(
                nome_fantasia=f"{nome} - {i}",
                razao_social=f"{nome} LTDA",
                cnpj=fake.cnpj(),
                email=fake.company_email(),
                telefone=fake.phone_number()[:30],
                cep=fake.postcode(),
                logradouro=fake.street_name(),
                numero=str(random.randint(1, 5000)),
                bairro=fake.bairro(),
                cidade=fake.city(),
                estado=fake.state_abbr(),
                pais="Brasil",
                data_abertura=date.today() - timedelta(days=random.randint(30, 365)),
                plano=p,
                plano_status=s,
                vencimento_assinatura=venc
            )
            db.session.add(est)
            db.session.flush()
            
            # Criar owner para cada est
            owner = Funcionario(
                estabelecimento_id=est.id,
                nome=fake.name(),
                username=f"owner_{est.id}",
                email=fake.email(),
                cargo="Proprietário",
                role="ADMIN",
                status="ativo",
                cpf=fake.cpf(),
                data_nascimento=fake.date_of_birth(minimum_age=25, maximum_age=55),
                celular=fake.phone_number()[:30],
                data_admissao=est.data_abertura,
                cep=est.cep,
                logradouro=est.logradouro,
                numero=est.numero,
                bairro=est.bairro,
                cidade=est.cidade,
                estado=est.estado,
                pais="Brasil"
            )
            owner.set_password("senha123")
            db.session.add(owner)

            # Configurações básicas obrigatórias
            config = Configuracao(
                estabelecimento_id=est.id,
                tema_escuro=True,
                cor_principal='#1F4E79',
                permitir_venda_sem_estoque=False,
                alerta_estoque_minimo=True
            )
            db.session.add(config)
            
        print(f"--- 15 novos Estabelecimentos (Tenants) criados com seus donos e configs.")

        db.session.commit()
        print("\n[FINISH] SEED SUPER ADMIN CONCLUÍDA COM SUCESSO!")
        print("-" * 50)
        print("DADOS DE ACESSO SUPER ADMIN:")
        print(f"  Login: rafaelmaldivas@gmail.com (ou maldivas)")
        print(f"  Senha: Mald1v@$")
        print("-" * 50)

    with app.app_context():
        internal_seed()

if __name__ == "__main__":
    seed_super_admin()
