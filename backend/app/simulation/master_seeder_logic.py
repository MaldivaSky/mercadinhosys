from datetime import date, timedelta
import os
import random
from app.models import db, Estabelecimento, Funcionario
from app.simulation.chronicle import ChronicleSimulator
from app.simulation.dna_factory import DNAFactory
from app.simulation.injectors import RealisticInjector
from flask import g

class MasterSeeder:
    @staticmethod
    def run_master_generation(app, months=6, fetch_cosmos=False):
        """
        Orquestração Master: HQ, Super Admin e Povoamento Industrial de Cenários.
        fetch_cosmos=True consulta a API Cosmos (1x) para enriquecer os EANs reais.
        """
        print("[MASTER SEEDER] - INICIANDO ENGENHARIA DE DADOS INDUSTRIAL")
        
        # 1. HQ MERCADINHOSYS (RAFAEL MALDIVAS)
        print("[HQ] Criando HQ e Super Admin (Rafael)...")
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
                nivel_acesso=1,
                is_super_admin=True,  # FIX: campo obrigatório para acesso superadmin
                status="ativo",
                cpf=os.environ.get("SEED_SUPERADMIN_CPF") or RealisticInjector.generate_cpf(),
                email="rafaelmaldivas@gmail.com",
                celular="(92) 99911-2233",
                data_nascimento=date(1985, 5, 20),
                data_admissao=date(2023, 1, 1),
                ativo=True
                # Funcionario não tem campos de endereço - removido **end_hq
            )
            # Senha NUNCA hardcoded (já vazou no histórico do git uma vez).
            _pwd = os.environ.get("SEED_SUPERADMIN_PASSWORD")
            if not _pwd:
                raise RuntimeError(
                    "SEED_SUPERADMIN_PASSWORD não definida no ambiente — "
                    "obrigatória para criar o super admin via seed."
                )
            # Tenta set_senha primeiro (padrão do modelo), fallback para set_password
            if hasattr(rafael, 'set_senha'):
                rafael.set_senha(_pwd)
            else:
                rafael.set_password(_pwd)
            db.session.add(rafael)
        else:
            # Garantir que um superadmin existente sempre tenha is_super_admin=True
            if not rafael.is_super_admin:
                rafael.is_super_admin = True
                rafael.status = "ativo"
                rafael.ativo = True
                print("[FIX] is_super_admin atualizado para maldivas existente.")
        
        db.session.commit()

        # 2. TENANTS (CONFIGURAÇÃO INDUSTRIAL)
        tenants_config = [
            {"id": "admin1", "caixa": "caixa1", "nome": "Mercado Maldivas Elite", "meses": 6, "dna": "ELITE"},
            {"id": "admin2", "caixa": "caixa2", "nome": "Supermercado Estrela", "meses": 3, "dna": "BOM"},
            {"id": "admin3", "caixa": "caixa3", "nome": "Vendas do Bairro", "meses": 1, "dna": "RAZOAVEL"},
            {"id": "admin4", "caixa": "caixa4", "nome": "Mercado Popular", "meses": 1, "dna": "MAL"},
            {"id": "admin5", "caixa": "caixa5", "nome": "Mini-Mercado Sucata", "meses": 1, "dna": "PESSIMO"}
        ]

        # Modo LIGHT (SEED_LIGHT=1): volume reduzido para Aiven/rede e teste de sincronização.
        # 2 lojas, 1 mês cada -> seed conclui pela internet e o sync do settings fica viável.
        import os as _os
        if _os.environ.get("SEED_LIGHT") == "1":
            tenants_config = [
                {"id": "admin1", "caixa": "caixa1", "nome": "Mercado Maldivas Elite", "meses": 1, "dna": "BOM"},
                {"id": "admin2", "caixa": "caixa2", "nome": "Supermercado Estrela", "meses": 1, "dna": "RAZOAVEL"},
            ]
            print("[MASTER] Modo LIGHT ativo: 2 lojas x 1 mes (volume reduzido).")

        simulator = ChronicleSimulator(app)

        for config in tenants_config:
            print(f"\n[PROVISIONANDO] {config['nome']} | {config['meses']} meses de história...")
            
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
                    cargo="Proprietário",
                    role="ADMIN",
                    nivel_acesso=1,
                    cpf=RealisticInjector.generate_cpf(),
                    email=f"{config['id']}@negocio.com",
                    celular="(92) 98888-0000",
                    data_nascimento=date(1980, 1, 1),
                    data_admissao=est.data_abertura,
                    ativo=True
                    # Funcionario não tem campos de endereço
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
                    role="CAIXA",
                    nivel_acesso=3,
                    salario_base=1600,
                    salario=1600,
                    cpf=RealisticInjector.generate_cpf(),
                    email=f"{config['caixa']}@negocio.com",
                    celular="(92) 97777-0000",
                    data_nascimento=date(1995, 1, 1),
                    data_admissao=est.data_abertura,
                    ativo=True
                    # Funcionario não tem campos de endereço
                )
                operador.set_password("caixa123")
                db.session.add(operador)

            # Estoque (nível 4) e RH (nível 5) — para demonstrar TODOS os níveis de
            # acesso do RBAC (o admin=1 e caixa=3 já existem; vendedor=7 vem do
            # seed_sfa). Assim há um usuário logável para cada papel na demo.
            n = config['id'].replace("admin", "")  # sufixo da loja: admin1 -> "1"
            extras = [
                {"u": f"estoque{n}", "nome": f"Estoquista {config['id'].upper()}",
                 "role": "ESTOQUE", "nivel": 4, "cargo": "Auxiliar de Estoque",
                 "senha": "estoque123", "cel": "(92) 96666-0000"},
                {"u": f"rh{n}", "nome": f"RH {config['id'].upper()}",
                 "role": "RH", "nivel": 5, "cargo": "Analista de RH",
                 "senha": "rh123", "cel": "(92) 95555-0000"},
            ]
            for ex in extras:
                if not Funcionario.query.filter_by(username=ex["u"]).first():
                    f_extra = Funcionario(
                        estabelecimento_id=est.id,
                        nome=ex["nome"],
                        username=ex["u"],
                        cargo=ex["cargo"],
                        role=ex["role"],
                        nivel_acesso=ex["nivel"],
                        salario_base=1800,
                        salario=1800,
                        cpf=RealisticInjector.generate_cpf(),
                        email=f"{ex['u']}@negocio.com",
                        celular=ex["cel"],
                        data_nascimento=date(1992, 1, 1),
                        data_admissao=est.data_abertura,
                        ativo=True,
                    )
                    f_extra.set_password(ex["senha"])
                    db.session.add(f_extra)

            db.session.commit()

            # 3. SIMULAÇÃO MASTER (CRONOLOGIA & NEGÓCIO)
            g.estabelecimento_id = est.id
            
            # Base Operacional
            RealisticInjector.inject_all_modules(est.id, fetch_cosmos=fetch_cosmos)
            
            # Motor de História
            print(f"[MOTOR] Rodando motor de simulação por {config['meses']} meses...")
            simulator.simulate_history(est, dna, config['meses'], dono.id)
            
        print("\n[SEED] [MAGNITUDE SÊNIOR] SEED CONCLUÍDA COM SUCESSO!")
        print("-" * 60)
        print("ACESSOS PARA DEMONSTRAÇÃO (por nível de acesso RBAC):")
        print("  Super Admin (SaaS)........: maldivas / (senha via SEED_SUPERADMIN_PASSWORD)")
        print("  Admin loja (nível 1)......: admin1..admin5 / admin123")
        print("  Caixa (nível 3)...........: caixa1..caixa5 / caixa123")
        print("  Estoque (nível 4).........: estoque1..estoque5 / estoque123")
        print("  RH (nível 5)..............: rh1..rh5 / rh123")
        print("  Vendedor (nível 7)........: rode seed_sfa.py (sfa_vend_a_<id> / 123456)")
        print("-" * 60)
