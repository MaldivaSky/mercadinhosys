import random
from datetime import date, timedelta
from decimal import Decimal
from app.models import db, Funcionario, Rota, Cliente
from app.simulation.injectors import RealisticInjector

class EnterpriseInjector:
    """
    Injetor de Especialidade Nível Enterprise.
    Responsável por estruturar a força de vendas externa (Vendedores de Rota),
    separar carteiras de clientes (Atacado B2B vs Varejo B2C) e regras avançadas.
    """

    @classmethod
    def inject_sfa_structure(cls, est_id):
        """Cria Vendedores, Rotas e distribui os Clientes B2B para eles."""
        print(f"   [ENTERPRISE INJECTOR] Estruturando SFA (Força de Vendas) para Est.{est_id}...")
        
        # 1. Injetar Vendedores com DNAs de Performance
        vendedores_dna = [
            {"nome": "Vendedor Alpha (Top)", "user": "vend_alpha", "dna": "TOP_PERFORMER"},
            {"nome": "Vendedor Beta (Médio)", "user": "vend_beta", "dna": "MEDIANO"},
            {"nome": "Vendedor Gama (Baixo)", "user": "vend_gama", "dna": "UNDERPERFORMER"}
        ]
        
        vendedores_obj = []
        for v_data in vendedores_dna:
            username = f"est{est_id}_{v_data['user']}"
            vend = Funcionario.query.filter_by(estabelecimento_id=est_id, username=username).first()
            if not vend:
                vend = Funcionario(
                    estabelecimento_id=est_id,
                    nome=v_data['nome'],
                    username=username,
                    cargo="Vendedor Externo",
                    role="VENDEDOR",
                    nivel_acesso=3, # Nível padrão de operação
                    cpf=RealisticInjector.generate_cpf(),
                    email=f"{username}@negocio.com.br",
                    celular=f"(92) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}",
                    data_nascimento=date(random.randint(1980, 2000), random.randint(1, 12), random.randint(1, 28)),
                    data_admissao=date.today() - timedelta(days=random.randint(180, 700)),
                    salario_base=Decimal("1500.00"),
                    salario=Decimal("1500.00"),
                    observacoes=v_data['dna'], # Usaremos isso para influenciar a simulação
                    status="ativo", ativo=True
                )
                if hasattr(vend, 'set_senha'):
                    vend.set_senha("senha123")
                else:
                    vend.set_password("senha123")
                db.session.add(vend)
                db.session.flush()
            vendedores_obj.append(vend)

        # 2. Criar Rotas e Vínculos
        dias_semana = [1, 2, 3, 4, 5] # Segunda a Sexta
        rotas_obj = []
        for i, vend in enumerate(vendedores_obj):
            nome_rota = f"Rota Zona {['Sul', 'Leste', 'Norte'][i]}"
            rota = Rota.query.filter_by(estabelecimento_id=est_id, nome=nome_rota).first()
            if not rota:
                rota = Rota(
                    estabelecimento_id=est_id,
                    nome=nome_rota,
                    vendedor_id=vend.id,
                    dia_semana=random.choice(dias_semana),
                    ativa=True
                )
                db.session.add(rota)
                db.session.flush()
            rotas_obj.append(rota)
            
        db.session.commit()
        
        # 3. Classificar Clientes (B2B Atacado vs B2C Varejo)
        clientes = Cliente.query.filter_by(estabelecimento_id=est_id).all()
        
        # Transformar 40% dos clientes em Atacado/B2B e associar aos Vendedores
        b2b_count = int(len(clientes) * 0.40)
        clientes_b2b = random.sample(clientes, b2b_count)
        
        for cli in clientes_b2b:
            # Distribuir desproporcionalmente para simular o "Top Performer" tendo a melhor carteira
            vend_escolhido = random.choices(
                vendedores_obj, 
                weights=[0.60, 0.30, 0.10], # 60% dos B2B pro Alpha, 30% pro Beta, 10% pro Gama
                k=1
            )[0]
            
            # Atualiza o cliente para ter um vendedor preferencial e limite de crédito alto
            # Se a coluna 'vendedor_id' não existir diretamente em Cliente, usaremos o 'observacoes' ou uma tag no nome por enquanto
            # Nota: O models.py do usuário pode ou não ter vendedor_id em Cliente, se não tiver, vamos atrelar na hora do PedidoVenda.
            cli.limite_credito = Decimal(str(random.randint(2000, 15000)))
            cli.observacoes = f"B2B|{vend_escolhido.id}" # Tag de roteirização
        
        db.session.commit()
        return vendedores_obj
