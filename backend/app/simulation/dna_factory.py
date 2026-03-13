import random
from datetime import datetime, timedelta
from app.models import db, Estabelecimento, Produto, Cliente, Venda, VendaItem, Pagamento, Caixa, MovimentacaoCaixa
from app.simulation.injectors import RealisticInjector

class ScenarioDNA:
    """Definição de comportamento de um estabelecimento"""
    def __init__(self, nome, margem_avg, giro_velocidade, inadimplencia_rate, ticket_medio, plano="Premium"):
        self.nome = nome
        self.margem_avg = margem_avg  # Multiplicador (ex: 1.3 = 30% margem)
        self.giro_velocidade = giro_velocidade # Vendas por dia
        self.inadimplencia_rate = inadimplencia_rate # % de inadimplência
        self.ticket_medio = ticket_medio
        self.plano = plano

class DNAFactory:
    """Fábrica de Realidade: Cria os 5 cenários do MercadinhoSys"""
    
    SCENARIOS = {
        "ELITE": ScenarioDNA("Mercado Maldivas Elite", 1.65, 180, 0.01, 155.0, "Enterprise"), # Alta eficiência
        "BOM": ScenarioDNA("Supermercado Estrela", 1.45, 120, 0.04, 95.0, "Premium"),    # Estável
        "RAZOAVEL": ScenarioDNA("Vendas do Bairro", 1.30, 50, 0.15, 55.0, "Pro"),    # Sobrevivendo
        "MAL": ScenarioDNA("Mercado Popular", 1.18, 25, 0.35, 35.0, "Basico"),         # Crise financeira
        "PESSIMO": ScenarioDNA("Mini-Mercado Sucata", 1.08, 8, 0.60, 18.0, "Starter")    # O caos (Inadimplência 60%)
    }

    @classmethod
    def get_dna(cls, scenario_key):
        return cls.SCENARIOS.get(scenario_key.upper())

    @classmethod
    def create_simulation_tenants(cls):
        """Cria os 5 estabelecimentos simulação se não existirem"""
        tenants = {}
        for key, dna in cls.SCENARIOS.items():
            est = Estabelecimento.query.filter_by(nome_fantasia=dna.nome).first()
            if not est:
                # Usar Endereço Real via ViaCEP Master
                end = RealisticInjector.get_endereco_by_cep("69005000") # Manaus Core
                est = Estabelecimento(
                    nome_fantasia=dna.nome,
                    razao_social=f"{dna.nome} EMPRESAS LTDA",
                    cnpj=f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
                    telefone="(92) 3000-0000",
                    email=f"contato@{key.lower()}.simulacao.com",
                    data_abertura=datetime.now().date() - timedelta(days=365),
                    plano=dna.plano,
                    **end
                )
                db.session.add(est)
                db.session.commit()
            tenants[key] = est
        return tenants
