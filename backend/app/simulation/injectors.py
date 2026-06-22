import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from app.models import (
    db, Estabelecimento, Funcionario, Produto, CategoriaProduto, Fornecedor, Cliente,
    ProdutoLote, ContaPagar, PedidoCompra, PedidoCompraItem, HistoricoPrecos, Auditoria,
    Beneficio, FuncionarioBeneficio, BancoHoras, ConfiguracaoHorario, Motorista, Veiculo,
    TaxaEntrega, DashboardMetrica, RelatorioAgendado, FuncionarioPreferencias, Despesa, utcnow
)
from app.simulation.cosmos_catalog import CosmosCatalog, normalize_ean
from app.decorators.rbac import ROLE_TO_NIVEL


class RealisticInjector:
    """Injetor de dados realistas brasileiros (regras de negócio MercadinhoSys)."""

    CEP_CACHE = {}

    # Catálogo de produtos com EANs reais (carregado uma vez por processo).
    _catalog = None

    # ── Fornecedores por especialidade (cada produto é linkado por categoria) ──
    FORNECEDORES_BASE = [
        {"key": "bebidas",    "fantasia": "Ambev Distribuição",        "razao": "Companhia de Bebidas das Américas LTDA"},
        {"key": "mercearia",  "fantasia": "Atacadão Secos e Molhados", "razao": "Atacadão Distribuição Comércio LTDA"},
        {"key": "laticinios", "fantasia": "Frios & Cia Distribuidora", "razao": "Frios e Laticínios Distribuição LTDA"},
        {"key": "limpeza",    "fantasia": "LimpaTudo Atacado",         "razao": "LimpaTudo Produtos de Limpeza LTDA"},
        {"key": "doces",      "fantasia": "Doce Sabor Distribuidora",  "razao": "Doce Sabor Comércio de Alimentos LTDA"},
    ]

    @staticmethod
    def round_qty(val):
        if val is None:
            return Decimal('0.000')
        return Decimal(str(val)).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP)

    @classmethod
    def get_catalog(cls, fetch_cosmos=False):
        if cls._catalog is None:
            cls._catalog = CosmosCatalog.load(fetch=fetch_cosmos)
        return cls._catalog

    # ------------------------------------------------------------------ #
    # Documentos / Endereços
    # ------------------------------------------------------------------ #
    @staticmethod
    def generate_cpf():
        cpf = [random.randint(0, 9) for _ in range(9)]
        for _ in range(2):
            val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
            cpf.append(11 - val if val > 1 else 0)
        return '%d%d%d.%d%d%d.%d%d%d-%d%d' % tuple(cpf)

    @staticmethod
    def generate_cnpj():
        n = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
        def dig(seq, pesos):
            s = sum(v * p for v, p in zip(seq, pesos))
            r = s % 11
            return 0 if r < 2 else 11 - r
        p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        p2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        d1 = dig(n, p1)
        d2 = dig(n + [d1], p2)
        n += [d1, d2]
        return '%d%d.%d%d%d.%d%d%d/%d%d%d%d-%d%d' % tuple(n)

    @classmethod
    def get_endereco_random(cls):
        cidades = [("Manaus", "AM", "69005-000"), ("São Paulo", "SP", "01001-000"), ("Belo Horizonte", "MG", "30140-010")]
        cid, uf, cep = random.choice(cidades)
        return {
            "cep": cep, "logradouro": "Rua Exemplo " + str(random.randint(1, 100)), "bairro": "Centro",
            "cidade": cid, "estado": uf, "numero": str(random.randint(1, 2000)), "pais": "Brasil"
        }

    # ------------------------------------------------------------------ #
    # Orquestrador
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_all_modules(cls, estabelecimento_id, fetch_cosmos=False):
        print(f"[SEED] Populando estabelecimento {estabelecimento_id}...")
        forns = cls.inject_fornecedores(estabelecimento_id)            # 1. Fornecedores (antes dos produtos)
        cls.inject_clientes(estabelecimento_id)                        # 2. Clientes
        cls.inject_funcionarios_time(estabelecimento_id)              # 3. Time completo (6 níveis RBAC)
        cls.inject_produtos_reais(estabelecimento_id, forns, fetch_cosmos)  # 4. Produtos linkados ao fornecedor
        cls.inject_rh_data(estabelecimento_id)                         # 5. RH (benefícios, banco de horas)
        cls.inject_delivery_data(estabelecimento_id)                   # 6. Delivery (motoristas, veículos)
        cls.inject_bi_data(estabelecimento_id)                         # 7. BI (métricas, relatórios)
        cls.inject_compras_financeiro(estabelecimento_id, forns)      # 8. Compras + contas a pagar
        cls.inject_despesas_setup(estabelecimento_id)                  # 9. Despesas de implantação
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 1. Fornecedores (por especialidade)
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_fornecedores(cls, est_id):
        """Cria fornecedores especializados. Retorna dict {especialidade: Fornecedor}."""
        forns = {}
        for base in cls.FORNECEDORES_BASE:
            end = cls.get_endereco_random()
            f = Fornecedor(
                estabelecimento_id=est_id,
                nome_fantasia=base["fantasia"],
                razao_social=base["razao"],
                cnpj=cls.generate_cnpj(),
                telefone="(92) 4004-8989",
                email=f"comercial@{base['key']}.com.br",
                contato_nome="Representante Comercial",
                contato_telefone="(92) 99888-7777",
                prazo_entrega=random.choice([3, 5, 7, 10]),
                forma_pagamento=random.choice(["30 DIAS", "28/35/42 DIAS", "À VISTA", "BOLETO 30 DIAS"]),
                classificacao=random.choice(["PREMIUM", "REGULAR", "REGULAR"]),
                **end
            )
            db.session.add(f)
            db.session.flush()
            forns[base["key"]] = f
        db.session.commit()
        return forns

    # ------------------------------------------------------------------ #
    # 2. Clientes
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_clientes(cls, est_id, count=50):
        primeiros = ["Maria", "José", "Ana", "João", "Antônio", "Francisca", "Carlos", "Paulo",
                     "Adriana", "Marcos", "Luiza", "Pedro", "Sandra", "Lucas", "Juliana", "Rafael"]
        sobren = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Almeida",
                  "Ferreira", "Rodrigues", "Gomes", "Martins", "Araújo", "Barbosa"]
        for _ in range(count):
            nome = f"{random.choice(primeiros)} {random.choice(sobren)}"
            limite = Decimal(str(random.choice([0, 0, 100, 200, 300, 500])))
            cli = Cliente(
                estabelecimento_id=est_id, nome=nome, cpf=cls.generate_cpf(),
                celular=f"(92) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}",
                email=f"{nome.lower().replace(' ', '.')}@email.com",
                limite_credito=limite, ativo=True,
                **cls.get_endereco_random()
            )
            db.session.add(cli)
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 3. Time completo com 6 níveis de acesso RBAC
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_funcionarios_time(cls, est_id):
        """
        Cria o time de apoio (Gerente, Estoque, RH, Entregador) e garante
        que TODOS os funcionários tenham nivel_acesso coerente com o role.
        O Admin (dono) e o Caixa já são criados pelo MasterSeeder.
        """
        time_config = [
            {"cargo": "Gerente",      "role": "GERENTE",    "user": "gerente",    "sal": 3500},
            {"cargo": "Estoquista",   "role": "ESTOQUE",    "user": "estoque",    "sal": 1700},
            {"cargo": "Analista RH",  "role": "RH",         "user": "rh",         "sal": 2800},
            {"cargo": "Entregador",   "role": "ENTREGADOR", "user": "entregador", "sal": 1600},
        ]
        for cfg in time_config:
            username = f"est{est_id}_{cfg['user']}"
            if Funcionario.query.filter_by(estabelecimento_id=est_id, username=username).first():
                continue
            f = Funcionario(
                estabelecimento_id=est_id,
                nome=f"{cfg['cargo']} {est_id}",
                username=username,
                cargo=cfg["cargo"],
                role=cfg["role"],
                nivel_acesso=ROLE_TO_NIVEL.get(cfg["role"], 3),
                cpf=cls.generate_cpf(),
                email=f"{username}@mercadinho.com.br",
                celular=f"(92) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}",
                data_nascimento=date(random.randint(1980, 2000), random.randint(1, 12), random.randint(1, 28)),
                data_admissao=date.today() - timedelta(days=random.randint(180, 700)),
                salario_base=Decimal(str(cfg["sal"])),
                salario=Decimal(str(cfg["sal"])),
                status="ativo", ativo=True
            )
            f.set_password("senha123")
            db.session.add(f)
            db.session.flush()
            db.session.add(FuncionarioPreferencias(
                estabelecimento_id=est_id, funcionario_id=f.id,
                tema_escuro=True, idioma="pt-BR", sidebar_colapsada=False
            ))

        # Sincroniza nivel_acesso de quem já existia (dono/caixa do MasterSeeder)
        for f in Funcionario.query.filter_by(estabelecimento_id=est_id).all():
            if not f.nivel_acesso or f.nivel_acesso == 0:
                f.nivel_acesso = ROLE_TO_NIVEL.get((f.role or "FUNCIONARIO").upper(), 3)
            if (f.salario_base is None or f.salario_base == 0) and (f.role or "").upper() in ("CAIXA", "FUNCIONARIO"):
                f.salario_base = Decimal("1600")
                f.salario = Decimal("1600")
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 4. Produtos — TODOS linkados a fornecedor (regra de negócio)
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_produtos_reais(cls, est_id, forns=None, fetch_cosmos=False):
        if forns is None:
            forns = {f.nome_fantasia: f for f in Fornecedor.query.filter_by(estabelecimento_id=est_id).all()}

        catalog = cls.get_catalog(fetch_cosmos)
        admin = Funcionario.query.filter_by(estabelecimento_id=est_id).first()

        # Categorias a partir do catálogo
        cat_cache = {}
        def get_cat(nome):
            if nome not in cat_cache:
                c = CategoriaProduto.query.filter_by(estabelecimento_id=est_id, nome=nome).first()
                if not c:
                    c = CategoriaProduto(estabelecimento_id=est_id, nome=nome)
                    db.session.add(c)
                    db.session.flush()
                cat_cache[nome] = c
            return cat_cache[nome]

        forn_keys = list(forns.keys())

        # Um produto REAL por SKU: nome, EAN, marca e NCM verdadeiros (sem variantes falsas)
        for variacao in [0]:
            for item in catalog:
                nome = item["n"]
                ean = item["ean"]
                marca = item.get("marca") or "Genérico"
                imagem = item.get("imagem") or ""

                # Fornecedor pela especialidade do produto
                forn = forns.get(item.get("forn")) or forns.get(random.choice(forn_keys))

                # Validade: 5% vencido, 15% vencendo, 80% ok
                r = random.random()
                if r < 0.05:
                    validade = date.today() - timedelta(days=random.randint(1, 20))
                elif r < 0.20:
                    validade = date.today() + timedelta(days=random.randint(0, 29))
                else:
                    validade = date.today() + timedelta(days=random.randint(30, 540))
                fabricacao = validade - timedelta(days=random.randint(120, 540))
                data_compra = date.today() - timedelta(days=random.randint(5, 45))
                data_receb = data_compra + timedelta(days=random.randint(1, (forn.prazo_entrega or 7)))

                preco_venda = Decimal(str(item["p"])) * (Decimal("1.0") if variacao == 0 else Decimal(str(round(random.uniform(0.85, 1.15), 2))))
                preco_venda = preco_venda.quantize(Decimal("0.01"))
                preco_custo = (preco_venda * Decimal("0.65")).quantize(Decimal("0.01"))
                margem = ((preco_venda - preco_custo) / preco_custo * 100).quantize(Decimal("0.01"))
                lote_str = f"LT-{est_id}-{uuid.uuid4().hex[:8].upper()}"
                qtd = random.randint(40, 400)

                p = Produto(
                    estabelecimento_id=est_id,
                    categoria_id=get_cat(item["cat"]).id,
                    fornecedor_id=forn.id,                       # ← REGRA: produto linkado a fornecedor
                    nome=nome,
                    descricao=f"{nome} — fornecido por {forn.nome_fantasia}.",
                    marca=marca,
                    fabricante=marca,
                    tipo="Nacional",
                    subcategoria=item["cat"],
                    unidade_medida=item["un"],
                    codigo_barras=ean,                           # ← EAN real (var.0) ou válido
                    codigo_interno=f"INT-{est_id}-{uuid.uuid4().hex[:6].upper()}",
                    preco_custo=preco_custo,
                    preco_venda=preco_venda,
                    margem_lucro=margem,
                    quantidade=qtd,
                    quantidade_minima=Decimal("20.000"),
                    ncm=item.get("ncm", "00000000"),
                    origem=0,
                    controlar_validade=True,
                    data_fabricacao=fabricacao,
                    data_validade=validade,
                    data_compra=data_compra,                     # ← novo campo
                    data_recebimento=data_receb,                 # ← novo campo
                    lote=lote_str,
                    ativo=True,
                    imagem_url=imagem or f"https://picsum.photos/seed/{abs(hash(nome))}/400/400"
                )
                db.session.add(p)
                db.session.flush()

                # Lote vinculado ao mesmo fornecedor
                db.session.add(ProdutoLote(
                    estabelecimento_id=est_id, produto_id=p.id, fornecedor_id=forn.id,
                    numero_lote=lote_str, quantidade=p.quantidade, quantidade_inicial=p.quantidade,
                    data_fabricacao=fabricacao, data_validade=validade, data_entrada=data_receb,
                    preco_custo_unitario=preco_custo, preco_venda=preco_venda, ativo=True
                ))

                # Histórico de preço inicial
                if admin:
                    db.session.add(HistoricoPrecos(
                        estabelecimento_id=est_id, produto_id=p.id, funcionario_id=admin.id,
                        preco_custo_anterior=(preco_custo * Decimal("0.9")).quantize(Decimal("0.01")),
                        preco_venda_anterior=(preco_venda * Decimal("0.9")).quantize(Decimal("0.01")),
                        margem_anterior=margem,
                        preco_custo_novo=preco_custo, preco_venda_novo=preco_venda, margem_nova=margem,
                        motivo="Cadastro inicial (entrada de mercadoria)"
                    ))
        db.session.commit()
        total = Produto.query.filter_by(estabelecimento_id=est_id).count()
        print(f"[SEED]   {total} produtos cadastrados (todos com fornecedor vinculado).")

    # ------------------------------------------------------------------ #
    # 5. RH (benefícios, banco de horas, grade horária)
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_rh_data(cls, est_id):
        from datetime import time as dt_time
        bens = [
            Beneficio(estabelecimento_id=est_id, nome="Vale Transporte", descricao="Auxílio deslocamento", valor_padrao=Decimal("200")),
            Beneficio(estabelecimento_id=est_id, nome="Vale Alimentação", descricao="Auxílio alimentação", valor_padrao=Decimal("450")),
            Beneficio(estabelecimento_id=est_id, nome="Plano de Saúde", descricao="Seguro saúde", valor_padrao=Decimal("350")),
        ]
        db.session.add_all(bens)
        db.session.flush()

        mes_ref = date.today().strftime("%Y-%m")
        for f in Funcionario.query.filter_by(estabelecimento_id=est_id).all():
            for b in bens:
                db.session.add(FuncionarioBeneficio(
                    estabelecimento_id=est_id, funcionario_id=f.id, beneficio_id=b.id,
                    valor=b.valor_padrao, ativo=True
                ))
            db.session.add(BancoHoras(
                estabelecimento_id=est_id, funcionario_id=f.id, mes_referencia=mes_ref,
                saldo_minutos=random.randint(-300, 900),
                horas_trabalhadas_minutos=random.randint(9000, 10200),
                horas_esperadas_minutos=9000, valor_hora_extra=Decimal("18.00")
            ))

        db.session.add(ConfiguracaoHorario(
            estabelecimento_id=est_id, hora_entrada=dt_time(8, 0), hora_saida_almoco=dt_time(12, 0),
            hora_retorno_almoco=dt_time(13, 0), hora_saida=dt_time(18, 0),
            tolerancia_entrada=10, exigir_foto=True
        ))
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 6. Delivery (taxas, motoristas, veículos)
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_delivery_data(cls, est_id):
        db.session.add_all([
            TaxaEntrega(estabelecimento_id=est_id, nome_regiao="Centro", taxa_fixa=Decimal("7.50"), taxa_por_km=Decimal("1.50"), tempo_estimado_minutos=25),
            TaxaEntrega(estabelecimento_id=est_id, nome_regiao="Bairros Nobres", taxa_fixa=Decimal("15.00"), taxa_por_km=Decimal("2.00"), tempo_estimado_minutos=40),
            TaxaEntrega(estabelecimento_id=est_id, nome_regiao="Periferia", taxa_fixa=Decimal("5.00"), taxa_por_km=Decimal("1.20"), tempo_estimado_minutos=50),
        ])
        m1 = Motorista(estabelecimento_id=est_id, nome="Carlos Entregador", cpf=cls.generate_cpf(),
                       cnh="12345678901", categoria_cnh="AB", tipo_vinculo="proprio",
                       celular="(92) 98123-4567", telefone="(92) 3234-5678", disponivel=True)
        m2 = Motorista(estabelecimento_id=est_id, nome="João Motoboy", cpf=cls.generate_cpf(),
                       cnh="09876543210", categoria_cnh="A", tipo_vinculo="terceirizado",
                       celular="(92) 99876-5432", telefone="(92) 3234-9999", disponivel=True)
        db.session.add_all([m1, m2])
        db.session.flush()
        db.session.add_all([
            Veiculo(estabelecimento_id=est_id, motorista_id=m1.id, tipo="carro", marca="Fiat", modelo="Uno",
                    placa=f"MSY{random.randint(1000,9999)}", consumo_medio=Decimal("8.5"), ativo=True),
            Veiculo(estabelecimento_id=est_id, motorista_id=m2.id, tipo="moto", marca="Honda", modelo="CG 160",
                    placa=f"MOT{random.randint(1000,9999)}", consumo_medio=Decimal("35.0"), ativo=True),
        ])
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 7. BI (métricas e relatórios agendados)
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_bi_data(cls, est_id):
        from datetime import time as dt_time
        db.session.add(RelatorioAgendado(
            estabelecimento_id=est_id, nome="Fechamento do Dia", tipo="vendas",
            formato="pdf", frequencia="diario", horario_envio=dt_time(22, 0),
            ativo=True, destinatarios_email=["rafaelmaldivas@gmail.com"]
        ))
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 8. Compras + Contas a Pagar (entrada de mercadoria inicial)
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_compras_financeiro(cls, est_id, forns=None):
        admin = Funcionario.query.filter_by(estabelecimento_id=est_id, role="ADMIN").first() \
            or Funcionario.query.filter_by(estabelecimento_id=est_id).first()
        if not admin:
            return

        forn_list = list(forns.values()) if forns else Fornecedor.query.filter_by(estabelecimento_id=est_id).all()
        if not forn_list:
            return

        # Um pedido de compra recebido por fornecedor, com sua conta a pagar (boleto)
        for forn in forn_list:
            prods = Produto.query.filter_by(estabelecimento_id=est_id, fornecedor_id=forn.id).limit(5).all()
            if not prods:
                continue
            pedido = PedidoCompra(
                estabelecimento_id=est_id, fornecedor_id=forn.id, funcionario_id=admin.id,
                numero_pedido=f"PC-{est_id}-{uuid.uuid4().hex[:5].upper()}",
                status="recebido", data_pedido=datetime.now() - timedelta(days=12),
                data_recebimento=date.today() - timedelta(days=8),
                condicao_pagamento=forn.forma_pagamento
            )
            db.session.add(pedido)
            db.session.flush()

            total = Decimal("0.00")
            for p in prods:
                qtd = Decimal("50")
                item_total = (p.preco_custo * qtd).quantize(Decimal("0.01"))
                db.session.add(PedidoCompraItem(
                    pedido_id=pedido.id, produto_id=p.id, produto_nome=p.nome,
                    estabelecimento_id=est_id, quantidade_solicitada=qtd, quantidade_recebida=qtd,
                    preco_unitario=p.preco_custo, total_item=item_total, status="recebido"
                ))
                total += item_total
            pedido.subtotal = total
            pedido.total = total

            db.session.add(ContaPagar(
                estabelecimento_id=est_id, fornecedor_id=forn.id, pedido_compra_id=pedido.id,
                numero_documento=f"NF-{random.randint(10000, 99999)}",
                tipo_documento="boleto",
                valor_original=total, valor_atual=total,
                data_emissao=date.today() - timedelta(days=8),
                data_vencimento=date.today() + timedelta(days=random.choice([5, 15, 22])),
                status="aberto"
            ))
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 9. Despesas de implantação (one-time)
    # ------------------------------------------------------------------ #
    @classmethod
    def inject_despesas_setup(cls, est_id):
        """Despesas iniciais que um empresário de primeira viagem tem ao abrir."""
        hoje = date.today()
        setup = [
            ("Reforma e adequação da loja", "Investimento", "fixa", 8500.00),
            ("Compra de gôndolas e prateleiras", "Investimento", "fixa", 4200.00),
            ("Freezer e geladeira expositora", "Investimento", "fixa", 6800.00),
            ("Sistema PDV e computador", "Investimento", "fixa", 3200.00),
            ("Taxa de abertura de empresa (contador)", "Administrativa", "fixa", 1500.00),
            # Despesa desnecessária para o sistema apontar
            ("Letreiro de neon importado premium", "Marketing", "variavel", 5500.00),
        ]
        for desc, cat, tipo, val in setup:
            db.session.add(Despesa(
                estabelecimento_id=est_id, descricao=desc, categoria=cat, tipo=tipo,
                valor=Decimal(str(val)), data_despesa=hoje - timedelta(days=random.randint(150, 180)),
                forma_pagamento=random.choice(["pix", "cartao_credito", "boleto"]),
                observacoes="Despesa de implantação do negócio"
            ))
        db.session.commit()
