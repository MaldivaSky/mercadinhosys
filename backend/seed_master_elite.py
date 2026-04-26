import os
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
import uuid
import json

# Configuração Master: Desativar Listeners e Sincronia para Performance Industrial
os.environ["FLASK_ENV"] = "simulation"
os.environ["SYNC_IN_PROGRESS"] = "1"

from app import create_app
from app.models import (
    db, Estabelecimento, Funcionario, Cliente, Produto, ProdutoLote,
    Fornecedor, RegistroPonto, ContaReceber, Auditoria, CategoriaProduto
)
from app.simulation.chronicle import ChronicleSimulator
from app.simulation.dna_factory import DNAFactory
from app.simulation.injectors import RealisticInjector
from flask import g
from werkzeug.security import generate_password_hash

def inject_ponto_history(estabelecimento_id, funcionario_id, months, current_date_limit):
    """Injeta histórico de ponto realista (Magnitude Sênior)"""
    start_date = current_date_limit - timedelta(days=months * 30)
    curr = start_date
    
    while curr <= current_date_limit:
        if curr.weekday() < 6: # Comercial (Seg-Sáb)
            # Entrada: ~08:00
            entrada_dt = datetime.combine(curr, datetime.min.time()) + timedelta(hours=8, minutes=random.randint(-15, 20))
            # Almoço Saída: ~12:00
            saida_almoco_dt = datetime.combine(curr, datetime.min.time()) + timedelta(hours=12, minutes=random.randint(-5, 10))
            # Almoço Volta: ~13:00
            volta_almoco_dt = saida_almoco_dt + timedelta(minutes=random.randint(55, 65))
            # Saída: ~18:00
            saida_dt = datetime.combine(curr, datetime.min.time()) + timedelta(hours=18, minutes=random.randint(-10, 45))
            
            eventos = [
                (entrada_dt.time(), "entrada"),
                (saida_almoco_dt.time(), "saida_intervalo"),
                (volta_almoco_dt.time(), "entrada_intervalo"),
                (saida_dt.time(), "saida")
            ]
            
            for hora, tipo in eventos:
                ponto = RegistroPonto(
                    estabelecimento_id=estabelecimento_id,
                    funcionario_id=funcionario_id,
                    data=curr if isinstance(curr, date) else curr.date(),
                    hora=hora,
                    tipo_registro=tipo,
                    status="normal" if random.random() > 0.1 else "atraso",
                    observacao="Registro automático Master Seed"
                )
                db.session.add(ponto)
        curr += timedelta(days=1)
    db.session.commit()

def pay_some_fiados(estabelecimento_id, inadimplencia_rate):
    """Liquida parte das contas a receber para simular fluxo de caixa real"""
    contas = ContaReceber.query.filter_by(estabelecimento_id=estabelecimento_id, status="aberto").all()
    for conta in contas:
        # Se não for devedor crônico (baseado na taxa de inadimplência do DNA)
        if random.random() > inadimplencia_rate:
            if conta.data_vencimento < date.today():
                conta.status = "pago"
                # Garantir Decimal para evitar Mismatch de Tipos
                valor = Decimal(str(conta.valor_atual))
                conta.valor_pago = valor
                conta.data_pagamento = conta.data_vencimento + timedelta(days=random.randint(0, 5))
    db.session.commit()

def run_master_elite_seed():
    app = create_app()
    with app.app_context():
        print("🚀 [MASTER SEED ELITE] - INICIANDO ENGENHARIA DE DADOS INDUSTRIAL")
        
        # 1. RESET ESTRATÉGICO
        print("🧹 Limpando tabelas core para reconstrução...")
        db.drop_all()
        db.create_all()

        # 2. HQ MERCADINHOSYS (RAFAEL MALDIVAS)
        print("👑 Criando HQ e Super Admin (Rafael)...")
        end_hq = {
            "cep": "69000-000", "logradouro": "Alameda Master SaaS", "numero": "1", 
            "bairro": "Distrito Industrial", "cidade": "Manaus", "estado": "AM", "pais": "Brasil"
        }
        hq = Estabelecimento(
            nome_fantasia="MercadinhoSys HQ",
            razao_social="MercadinhoSys SaaS Technology LTDA",
            cnpj="00.000.000/0001-00",
            email="rafaelmaldivas@gmail.com",
            telefone="(92) 99999-0000",
            data_abertura=date(2023, 1, 1), 
            plano="Premium Master", # Role de Negócio
            plano_status="ativo",
            **end_hq
        )
        db.session.add(hq)
        db.session.flush()

        rafael = Funcionario(
            estabelecimento_id=hq.id,
            nome="Rafael Maldivas",
            username="maldivas",
            senha=generate_password_hash("Mald1v@$"),
            cargo="SUPER ADMIN",
            role="ADMIN", # Requerido para is_super_admin retornar True
            is_super_admin=True,
            cpf=RealisticInjector.generate_cpf(), # CPF Válido para passar no modelo
            email="rafaelmaldivas@gmail.com",
            celular="(92) 99911-2233",
            data_nascimento=date(1985, 5, 20),
            data_admissao=date(2023, 1, 1),
            ativo=True,
            **end_hq
        )
        db.session.add(rafael)
        db.session.commit()

        # 3. TENANTS (CONFIGURAÇÃO EXAUSTIVA)
        tenants_config = [
            {"id": "admin1", "caixa": "caixa1", "nome": "Souza Center (Premium)", "meses": 6, "dna": "ELITE"},
            {"id": "admin2", "caixa": "caixa2", "nome": "Mercadinho do Bairro", "meses": 3, "dna": "BOM"},
            {"id": "admin3", "caixa": "caixa3", "nome": "Hortifruti da Villa", "meses": 1, "dna": "RAZOAVEL"}
        ]

        simulator = ChronicleSimulator(app)

        for config in tenants_config:
            print(f"\n📦 [PROVISIONANDO] {config['nome']} | {config['meses']} meses de história...")
            
            dna = DNAFactory.get_dna(config['dna'])
            end_tenant = RealisticInjector.get_endereco_random()
            
            est = Estabelecimento(
                nome_fantasia=config['nome'],
                razao_social=f"{config['nome']} LTDA",
                cnpj=f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
                telefone=f"(92) 3{random.randint(100,999)}-{random.randint(1000,9999)}",
                email=f"contato@{config['id']}.com.br",
                data_abertura=date.today() - timedelta(days=config['meses']*30),
                plano=dna.plano,
                plano_status="ativo",
                **end_tenant
            )
            db.session.add(est)
            db.session.flush()
            
            # Dono (Owner)
            dono = Funcionario(
                estabelecimento_id=est.id,
                nome=f"Dono {config['id'].upper()}",
                username=config['id'],
                senha=generate_password_hash("admin123"),
                cargo="Gerente Geral",
                role="ADMIN",
                cpf=RealisticInjector.generate_cpf(),
                email=f"{config['id']}@negocio.com",
                celular="(92) 98888-0000",
                data_nascimento=date(1980, 1, 1),
                data_admissao=est.data_abertura,
                ativo=True,
                **end_tenant
            )
            db.session.add(dono)
            
            # Caixa (Employee)
            operador = Funcionario(
                estabelecimento_id=est.id,
                nome=f"Operador {config['caixa'].upper()}",
                username=config['caixa'],
                senha=generate_password_hash("caixa123"),
                cargo="Caixa PDV",
                role="FUNCIONARIO",
                cpf=RealisticInjector.generate_cpf(),
                email=f"{config['caixa']}@negocio.com",
                celular="(92) 97777-0000",
                data_nascimento=date(1995, 1, 1),
                data_admissao=est.data_abertura,
                ativo=True,
                **end_tenant
            )
            db.session.add(operador)
            db.session.commit()

            # 4. SIMULAÇÃO MASTER (CRONOLOGIA & NEGÓCIO)
            g.estabelecimento_id = est.id
            
            # Base Operacional
            RealisticInjector.inject_fornecedores(est.id)
            RealisticInjector.inject_clientes(est.id, count=60)
            RealisticInjector.inject_produtos_reais(est.id)
            
            # Motor de História (Vendas, Lotes, Validade, Despesas)
            print(f"📈 Rodando motor de simulação por {config['meses']} meses...")
            simulator.simulate_history(est, dna, config['meses'], dono.id)
            
            # Injeção Extra: RH Ponto (Industrial)
            print("🕒 Injetando histórico de Ponto RH...")
            inject_ponto_history(est.id, operador.id, config['meses'], date.today())
            
            # Injeção Extra: Liquidação de Fiados (Fluxo Real)
            print("💰 Liquidando faturas de Fiado (Bons Pagadores)...")
            pay_some_fiados(est.id, dna.inadimplencia_rate)

        print("\n\n🏆 [MAGNITUDE SÊNIOR] SEED CONCLUÍDA COM SUCESSO!")
        print("-" * 60)
        print("ACESSO SUPER ADMIN:")
        print("Username: maldivas | Senha: Mald1v@$")
        print("\nCLIENTES PARA TESTE:")
        print("1. admin1 / admin123 (6 meses - Premium)")
        print("2. admin2 / admin123 (3 meses - Médio)")
        print("3. admin3 / admin123 (1 mês - Novo)")
        print("\nOPERADORES:")
        print("caixa1, caixa2, caixa3 / caixa123")
        print("-" * 60)

if __name__ == "__main__":
    run_master_elite_seed()
