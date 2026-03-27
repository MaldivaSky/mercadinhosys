import random
import uuid
import requests
import time
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from app.models import (
    db, Estabelecimento, Funcionario, Produto, CategoriaProduto, Fornecedor, Cliente, 
    ProdutoLote, ContaPagar, PedidoCompra, PedidoCompraItem, HistoricoPrecos, Auditoria,
    Beneficio, FuncionarioBeneficio, BancoHoras, ConfiguracaoHorario, Motorista, Veiculo,
    TaxaEntrega, DashboardMetrica, RelatorioAgendado, FuncionarioPreferencias, utcnow
)

class RealisticInjector:
    """Injetor de dados realistas brasileiros (UNIVERSAL MASTER GRADE - Magnitude CTO)"""
    
    CEP_CACHE = {}

    @staticmethod
    def round_qty(val):
        if val is None: return Decimal('0.000')
        return Decimal(str(val)).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP)

    # DATABASE DE SKUS REALISTAS (100+ ITENS)
    SKU_DB = [
        # --- AÇOUGUE/PEIXARIA (KG) ---
        {"n": "Picanha Bovina Maturatta", "cat": "Açougue", "un": "KG", "p": 89.90, "ncm": "02013000"},
        {"n": "Contra-Filé Bovino", "cat": "Açougue", "un": "KG", "p": 45.90, "ncm": "02013000"},
        {"n": "Alcatra com Maminha", "cat": "Açougue", "un": "KG", "p": 42.90, "ncm": "02013000"},
        {"n": "Acém Moído Primeira", "cat": "Açougue", "un": "KG", "p": 28.50, "ncm": "02013000"},
        {"n": "Peito de Frango Sadia 1kg", "cat": "Açougue", "un": "PC", "p": 21.90, "ncm": "02071210"},
        {"n": "Linguiça Toscana Sadia", "cat": "Açougue", "un": "KG", "p": 24.50, "ncm": "16010000"},
        {"n": "Filé de Tilápia 500g", "cat": "Açougue", "un": "PC", "p": 34.90, "ncm": "03046100"},
        # --- HORTIFRUTI (KG) ---
        {"n": "Tomate Italiano", "cat": "Hortifruti", "un": "KG", "p": 8.50, "ncm": "07020000"},
        {"n": "Cebola Branca", "cat": "Hortifruti", "un": "KG", "p": 5.40, "ncm": "07031011"},
        {"n": "Batata Inglesa", "cat": "Hortifruti", "un": "KG", "p": 6.90, "ncm": "07019000"},
        {"n": "Banana Prata", "cat": "Hortifruti", "un": "KG", "p": 5.80, "ncm": "08031000"},
        {"n": "Maçã Gala", "cat": "Hortifruti", "un": "KG", "p": 12.50, "ncm": "08081000"},
        {"n": "Alface Crespa", "cat": "Hortifruti", "un": "UN", "p": 3.50, "ncm": "07051900"},
        # --- PADARIA (UN/KG) ---
        {"n": "Pão Francês", "cat": "Padaria", "un": "KG", "p": 16.90, "ncm": "19059090"},
        {"n": "Pão de Forma Pullman", "cat": "Padaria", "un": "UN", "p": 8.90, "ncm": "19059010"},
        {"n": "Bolo de Fubá Caseiro", "cat": "Padaria", "un": "UN", "p": 12.00, "ncm": "19059090"},
        # --- LATICÍNIOS ---
        {"n": "Leite UHT 1L", "cat": "Laticínios", "un": "UN", "p": 5.45, "ncm": "04012010"},
        {"n": "Queijo Mussarela Fatiado", "cat": "Laticínios", "un": "KG", "p": 48.90, "ncm": "04069010"},
        {"n": "Manteiga Aviação 200g", "cat": "Laticínios", "un": "UN", "p": 15.90, "ncm": "04051000"},
        # --- MERCEARIA ---
        {"n": "Arroz Tio João 5kg", "cat": "Mercearia", "un": "PC", "p": 28.90, "ncm": "10063011"},
        {"n": "Feijão Kicaldo 1kg", "cat": "Mercearia", "un": "UN", "p": 8.45, "ncm": "07133399"},
        {"n": "Café Pilão 500g", "cat": "Mercearia", "un": "UN", "p": 18.90, "ncm": "09012100"},
        {"n": "Macarrão Galo 500g", "cat": "Mercearia", "un": "UN", "p": 4.50, "ncm": "19021900"},
        # --- LIMPEZA ---
        {"n": "Detergente Ypê 500ml", "cat": "Limpeza", "un": "UN", "p": 2.59, "ncm": "34022000"},
        {"n": "Omo Lavagem Perfeita 1.6kg", "cat": "Limpeza", "un": "PC", "p": 22.90, "ncm": "34022000"}
    ]

    @staticmethod
    def generate_cpf():
        cpf = [random.randint(0, 9) for _ in range(9)]
        for _ in range(2):
            val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
            cpf.append(11 - val if val > 1 else 0)
        return '%d%d%d.%d%d%d.%d%d%d-%d%d' % tuple(cpf)

    @classmethod
    def get_endereco_random(cls):
        cidades = [("Manaus", "AM", "69005-000"), ("São Paulo", "SP", "01001-000"), ("BH", "MG", "30140-010")]
        cid, uf, cep = random.choice(cidades)
        return {
            "cep": cep, "logradouro": "Rua Exemplo " + str(random.randint(1,100)), "bairro": "Centro",
            "cidade": cid, "estado": uf, "numero": str(random.randint(1, 2000)), "pais": "Brasil"
        }

    @classmethod
    def inject_all_modules(cls, estabelecimento_id):
        """Orquestrador Master de Injeção em TODAS as tabelas"""
        print(f"🏢 Popolando Estabelecimento {estabelecimento_id} (Universal Seeder)...")
        # 1. Foundation
        forns = cls.inject_fornecedores(estabelecimento_id)
        cls.inject_clientes(estabelecimento_id)
        cls.inject_funcionarios_time(estabelecimento_id, "ELITE" if estabelecimento_id == 1 else None)
        
        # 2. Operacional
        cls.inject_produtos_reais(estabelecimento_id)
        
        # 3. RH Master
        cls.inject_rh_data(estabelecimento_id)
        
        # 4. Delivery Master
        cls.inject_delivery_data(estabelecimento_id)
        
        # 5. Financeiro/BI Master
        cls.inject_bi_data(estabelecimento_id)
        
        # 6. Compras e Contas a Pagar
        cls.inject_compras_financeiro(estabelecimento_id)
        db.session.commit()

    @classmethod
    def inject_compras_financeiro(cls, est_id):
        from app.models import PedidoCompra, PedidoCompraItem, ContaPagar
        admin = Funcionario.query.filter_by(estabelecimento_id=est_id, role="ADMIN").first()
        forn = Fornecedor.query.filter_by(estabelecimento_id=est_id).first()
        prods = Produto.query.filter_by(estabelecimento_id=est_id).limit(5).all()
        
        if not (admin and forn and prods): return

        # 1. Pedido de Compra
        valor_total = Decimal("1500.00")
        pedido = PedidoCompra(
            estabelecimento_id=est_id, fornecedor_id=forn.id, funcionario_id=admin.id,
            numero_pedido=f"PC-{random.randint(1000, 9999)}",
            status="recebido", total=valor_total,
            data_pedido=datetime.now() - timedelta(days=10),
            data_recebimento=date.today() - timedelta(days=1)
        )
        db.session.add(pedido)
        db.session.flush()

        for p in prods:
            db.session.add(PedidoCompraItem(
                pedido_id=pedido.id, produto_id=p.id, produto_nome=p.nome,
                quantidade_solicitada=Decimal("50.000"), preco_unitario=p.preco_custo,
                total_item=p.preco_custo * Decimal("50"), status="recebido"
            ))

        # 2. Conta a Pagar vinculada
        cp = ContaPagar(
            estabelecimento_id=est_id, fornecedor_id=forn.id, pedido_compra_id=pedido.id,
            numero_documento=f"NF-{random.randint(10000, 99999)}",
            valor_original=valor_total, valor_atual=valor_total,
            data_emissao=date.today() - timedelta(days=10),
            data_vencimento=date.today() + timedelta(days=20),
            status="aberto"
        )
        db.session.add(cp)

    @classmethod
    def inject_rh_data(cls, est_id):
        from datetime import time as dt_time
        # 1. Benefícios
        bens = [
            Beneficio(estabelecimento_id=est_id, nome="Vale Transporte", descricao="Auxílio deslocamento", valor_padrao=200),
            Beneficio(estabelecimento_id=est_id, nome="Vale Refeição", descricao="Auxílio alimentação", valor_padrao=450),
            Beneficio(estabelecimento_id=est_id, nome="Plano de Saúde", descricao="Seguro saúde Bradesco", valor_padrao=350)
        ]
        db.session.add_all(bens)
        db.session.flush()

        # 2. Atribuir ao time
        funcs = Funcionario.query.filter_by(estabelecimento_id=est_id).all()
        for f in funcs:
            for b in bens:
                fb = FuncionarioBeneficio(funcionario_id=f.id, beneficio_id=b.id, valor=b.valor_padrao, ativo=True)
                db.session.add(fb)
            
            # Banco Horas (Histórico)
            bh = BancoHoras(
                funcionario_id=f.id, mes_referencia="2024-03", 
                saldo_minutos=600, # 10 horas
                horas_trabalhadas_minutos=9600, # 160h
                horas_esperadas_minutos=9000, # 150h
                valor_hora_extra=Decimal("150.00")
            )
            db.session.add(bh)

        # 3. Grade Horária (Campos REAIS de models.py)
        ch = ConfiguracaoHorario(
            estabelecimento_id=est_id,
            hora_entrada=dt_time(8,0), 
            hora_saida_almoco=dt_time(12,0),
            hora_retorno_almoco=dt_time(13,0),
            hora_saida=dt_time(18,0),
            tolerancia_entrada=10, exigir_foto=True
        )
        db.session.add(ch)

    @classmethod
    def inject_delivery_data(cls, est_id):
        """Injeta motoristas e veículos profissionais (Magnitude Senior)."""
        # 1. Taxas Realistas
        db.session.add_all([
            TaxaEntrega(estabelecimento_id=est_id, nome_regiao="Centro Histórico", taxa_fixa=Decimal("7.50"), taxa_por_km=Decimal("1.50"), tempo_estimado_minutos=25),
            TaxaEntrega(estabelecimento_id=est_id, nome_regiao="Bairros Nobres", taxa_fixa=Decimal("15.00"), taxa_por_km=Decimal("2.00"), tempo_estimado_minutos=40),
            TaxaEntrega(estabelecimento_id=est_id, nome_regiao="Periferia", taxa_fixa=Decimal("5.00"), taxa_por_km=Decimal("1.20"), tempo_estimado_minutos=50)
        ])

        # 2. Motoristas (Equipe Diversificada)
        m1 = Motorista(
            estabelecimento_id=est_id, nome="Carlos Entregador", cpf=cls.generate_cpf(), 
            cnh="1234567890", categoria_cnh="AB", tipo_vinculo="proprio", celular="(92) 98123-4567",
            telefone="(92) 3234-5678", disponivel=True
        )
        m2 = Motorista(
            estabelecimento_id=est_id, nome="João Motoboy", cpf=cls.generate_cpf(),
            cnh="0987654321", categoria_cnh="A", tipo_vinculo="terceirizado", celular="(92) 99876-5432",
            telefone="(92) 3234-9999", disponivel=True
        )
        db.session.add_all([m1, m2])
        db.session.flush()

        # 3. Veículos (Moto e Carro com Consumo)
        v1 = Veiculo(
            estabelecimento_id=est_id, motorista_id=m1.id, tipo="carro", marca="Fiat", modelo="Uno", 
            placa="MSY-2024", consumo_medio=Decimal("8.5"), ativo=True
        )
        v2 = Veiculo(
            estabelecimento_id=est_id, motorista_id=m2.id, tipo="moto", marca="Honda", modelo="CG 160", 
            placa="MOT-2024", consumo_medio=Decimal("35.0"), ativo=True
        )
        db.session.add_all([v1, v2])
        db.session.commit()

    @classmethod
    def inject_bi_data(cls, est_id):
        # 1. Métricas (Last 30 days)
        for i in range(30):
            d = date.today() - timedelta(days=i)
            m = DashboardMetrica(
                estabelecimento_id=est_id, data_referencia=d,
                total_vendas_dia=Decimal(random.randint(2000, 8000)),
                ticket_medio_dia=Decimal(random.randint(45, 120)),
                quantidade_vendas_dia=random.randint(20, 100),
                clientes_atendidos_dia=random.randint(1, 10)
            )
            db.session.add(m)

        # 2. Relatórios Agendados
        from datetime import time as dt_time
        ra = RelatorioAgendado(
            estabelecimento_id=est_id, nome="Fechamento do Dia", tipo="vendas",
            formato="pdf", frequencia="diario", horario_envio=dt_time(22, 0),
            ativo=True, destinatarios_email=["rafaelmaldivas@gmail.com"]
        )
        db.session.add(ra)

    @classmethod
    def inject_fornecedores(cls, est_id):
        nomes = ["Seara Distribuição", "Ambev Manaus", "Nestlé Professional"]
        objs = []
        for n in nomes:
            f = Fornecedor(estabelecimento_id=est_id, nome_fantasia=n, razao_social=f"{n} S.A.", cnpj=f"12.345.678/0001-{random.randint(10,99)}", **cls.get_endereco_random())
            f.telefone = "(92) 4004-8989"
            f.email = f"comercial@{n.lower().replace(' ', '')}.com"
            db.session.add(f)
            objs.append(f)
        db.session.commit()
        return objs

    @classmethod
    def inject_clientes(cls, est_id, count=50):
        for _ in range(count):
            cli = Cliente(estabelecimento_id=est_id, nome=f"Cliente {random.randint(100,999)}", cpf=cls.generate_cpf(), celular="(92) 99999-0000", **cls.get_endereco_random())
            db.session.add(cli)

    @classmethod
    def inject_funcionarios_time(cls, est_id, scenario_key=None):
        from werkzeug.security import generate_password_hash
        time_config = [{"c": "Gerente", "u": "admin", "r": "ADMIN"}]
        for config in time_config:
            username = config['u'] if scenario_key else f"est{est_id}_{config['u']}"
            f = Funcionario(
                estabelecimento_id=est_id, nome=f"Admin {est_id}", username=username, cargo=config['c'],
                role=config['r'], cpf=cls.generate_cpf(), email=f"{username}@mercadinho.com.br",
                celular="(11) 98888-7777", data_nascimento=date(1990,1,1), data_admissao=date(2023,1,1),
                salario_base=3000, ativo=True, **cls.get_endereco_random()
            )
            f.set_password("admin123" if not scenario_key else "adminElite123")
            db.session.add(f)
            db.session.flush()
            # Preferências
            pref = FuncionarioPreferencias(funcionario_id=f.id, tema_escuro=True, idioma="pt-BR", sidebar_colapsada=False)
            db.session.add(pref)

    @classmethod
    def inject_produtos_reais(cls, est_id):
        cat = CategoriaProduto.query.filter_by(estabelecimento_id=est_id).first()
        if not cat:
            cat = CategoriaProduto(estabelecimento_id=est_id, nome="Geral")
            db.session.add(cat)
            db.session.flush()
        
        # Gerar 130 SKUs por Tenant — SEM LIMITACOES (5 variacoes x 26 SKUs base)
        for variacao in range(5):
            for item in cls.SKU_DB:
                marca = f" - Marca {variacao}" if variacao > 0 else ""
                vencimento = date.today() + timedelta(days=random.randint(10, 400))

                p = Produto(
                    estabelecimento_id=est_id, categoria_id=cat.id, nome=item["n"] + marca,
                    codigo_barras=f"789{abs(hash(item['n'] + marca)) % 1000000000:010d}",
                    codigo_interno=f"INT-{uuid.uuid4().hex[:4]}", unidade_medida=item["un"],
                    preco_custo=Decimal(str(item["p"])) * Decimal("0.7"), preco_venda=Decimal(str(item["p"])),
                    quantidade=random.randint(50, 500), ativo=True, controlar_validade=True,
                    data_validade=vencimento, lote=f"LT-{uuid.uuid4().hex[:4].upper()}"
                )
                db.session.add(p)
                db.session.flush()

                lote = ProdutoLote(
                    estabelecimento_id=est_id, produto_id=p.id, numero_lote=p.lote,
                    quantidade=p.quantidade, quantidade_inicial=p.quantidade,
                    data_validade=p.data_validade, preco_custo_unitario=p.preco_custo, ativo=True
                )
                db.session.add(lote)

                hp = HistoricoPrecos(
                    estabelecimento_id=est_id, produto_id=p.id,
                    funcionario_id=Funcionario.query.filter_by(estabelecimento_id=est_id).first().id,
                    preco_custo_anterior=p.preco_custo, preco_venda_anterior=p.preco_venda, margem_anterior=40,
                    preco_custo_novo=p.preco_custo, preco_venda_novo=p.preco_venda, margem_nova=40, motivo="Initial Seed"
                )
                db.session.add(hp)
