from datetime import date, timedelta
import random
from app.models import db, Estabelecimento, Funcionario
from app.simulation.chronicle import ChronicleSimulator
from app.simulation.dna_factory import DNAFactory
from app.simulation.injectors import RealisticInjector
from flask import g

class MasterSeeder:
    @staticmethod
    def run_master_generation(app, months=6):
        """
        Orquestração Master: HQ, Super Admin e Povoamento Industrial de Cenários.
        """
        print("🚀 [MASTER SEEDER] - INICIANDO ENGENHARIA DE DADOS INDUSTRIAL")
        
        # 1. HQ MERCADINHOSYS (RAFAEL MALDIVAS)
        print("👑 Criando HQ e Super Admin (Rafael)...")
        end_hq = {
            "cep": "69000-000", "logradouro": "Alameda Master SaaS", "numero": "1", 
            "bairro": "Distrito Industrial", "cidade": "Manaus", "estado": "AM", "pais": "Brasil"
        }
        
        hq = Estabelecimento.query.filter_by(cnpj="00000000000100").first()
        if not hq:
            hq = Estabelecimento(
                nome_fantasia="MercadinhoSys HQ",
                razao_social="MercadinhoSys SaaS Technology LTDA",
                cnpj="00000000000100",
                email="rafaelmaldivas@gmail.com",
                telefone="(92) 99999-0000",
                data_abertura=date(2023, 1, 1), 
                plano="Premium Master",
                plano_status="ativo",
                **end_hq
            )
            db.session.add(hq)
            db.session.flush()

        rafael = Funcionario.query.filter_by(username="maldivas").first()
        if not rafael:
            rafael = Funcionario(
                estabelecimento_id=hq.id,
                nome="Rafael Maldivas",
                username="maldivas",
                cargo="SUPER ADMIN",
                role="ADMIN",
                cpf=RealisticInjector.generate_cpf(),
                email="rafaelmaldivas@gmail.com",
                celular="(92) 99911-2233",
                data_nascimento=date(1985, 5, 20),
                data_admissao=date(2023, 1, 1),
                ativo=True,
                **end_hq
            )
            rafael.set_password("Mald1v@$")
            db.session.add(rafael)
        
        db.session.commit()

        # 2. TENANTS (CONFIGURAÇÃO INDUSTRIAL)
        tenants_config = [
            {"id": "admin1", "caixa": "caixa1", "nome": "Mercado Maldivas Elite", "meses": 6, "dna": "ELITE"},
            {"id": "admin2", "caixa": "caixa2", "nome": "Supermercado Estrela", "meses": 3, "dna": "BOM"},
            {"id": "admin3", "caixa": "caixa3", "nome": "Vendas do Bairro", "meses": 1, "dna": "RAZOAVEL"},
            {"id": "admin4", "caixa": "caixa4", "nome": "Mercado Popular", "meses": 1, "dna": "MAL"},
            {"id": "admin5", "caixa": "caixa5", "nome": "Mini-Mercado Sucata", "meses": 1, "dna": "PESSIMO"}
        ]

        simulator = ChronicleSimulator(app)

        for config in tenants_config:
            print(f"\n📦 [PROVISIONANDO] {config['nome']} | {config['meses']} meses de história...")
            
            dna = DNAFactory.get_dna(config['dna'])
            end_tenant = RealisticInjector.get_endereco_random()
            
            est = Estabelecimento.query.filter_by(nome_fantasia=config['nome']).first()
            if not est:
                est = Estabelecimento(
                    nome_fantasia=config['nome'],
                    razao_social=f"{config['nome']} LTDA",
                    cnpj=DNAFactory.CNPJ_SIMULACAO.get(config['dna'], f'99.{random.randint(100,999)}.000/0001-00'),
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
            dono = Funcionario.query.filter_by(username=config['id']).first()
            if not dono:
                dono = Funcionario(
                    estabelecimento_id=est.id,
                    nome=f"Dono {config['id'].upper()}",
                    username=config['id'],
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
                dono.set_password("admin123")
                db.session.add(dono)
            
            # Caixa (Employee)
            operador = Funcionario.query.filter_by(username=config['caixa']).first()
            if not operador:
                operador = Funcionario(
                    estabelecimento_id=est.id,
                    nome=f"Operador {config['caixa'].upper()}",
                    username=config['caixa'],
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
                operador.set_password("caixa123")
                db.session.add(operador)
            
            db.session.commit()

            # 3. SIMULAÇÃO MASTER (CRONOLOGIA & NEGÓCIO)
            g.estabelecimento_id = est.id
            
            # Base Operacional
            RealisticInjector.inject_all_modules(est.id)
            
            # Motor de História
            print(f"📈 Rodando motor de simulação por {config['meses']} meses...")
            simulator.simulate_history(est, dna, config['meses'], dono.id)
            
        print("\n🏆 [MAGNITUDE SÊNIOR] SEED CONCLUÍDA COM SUCESSO!")
