import random
import uuid
import requests
import time
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from app.models import (
    db, Estabelecimento, Funcionario, Produto, CategoriaProduto, Fornecedor, Cliente, 
    ProdutoLote, ContaPagar, utcnow
)

class RealisticInjector:
    """Injetor de dados realistas brasileiros (MASTER GRADE - Magnitude Senior)"""
    
    # Cache de CEPs para evitar excesso de requisições e garantir velocidade MASTER
    CEP_CACHE = {}

    @staticmethod
    def round_qty(val):
        if val is None: return Decimal('0.000')
        return Decimal(str(val)).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP)

    SKU_DB = [
        # --- AÇOUGUE (KG) ---
        {"n": "Picanha Bovina Especial", "cat": "Açougue", "un": "KG", "code": "1001", "p": 79.90, "ncm": "02013000"},
        {"n": "Contra-Filé Bovino", "cat": "Açougue", "un": "KG", "code": "1002", "p": 45.90, "ncm": "02013000"},
        {"n": "Alcatra com Maminha", "cat": "Açougue", "un": "KG", "code": "1003", "p": 42.90, "ncm": "02013000"},
        {"n": "Acém Moído Primeira", "cat": "Açougue", "un": "KG", "code": "1004", "p": 28.50, "ncm": "02013000"},
        {"n": "Coxão Mole Resfriado", "cat": "Açougue", "un": "KG", "code": "1005", "p": 36.90, "ncm": "02013000"},
        {"n": "Frango Inteiro Resfriado", "cat": "Açougue", "un": "KG", "code": "1006", "p": 12.90, "ncm": "02071100"},
        {"n": "Peito de Frango Sadia 1kg", "cat": "Açougue", "un": "PC", "code": "7891515431101", "p": 21.90, "ncm": "02071210"},
        {"n": "Linguiça Toscana Sadia", "cat": "Açougue", "un": "KG", "code": "7891515433006", "p": 24.50, "ncm": "16010000"},

        # --- HORTIFRUTI (KG) ---
        {"n": "Tomate Italiano", "cat": "Hortifruti", "un": "KG", "code": "2001", "p": 8.50, "ncm": "07020000"},
        {"n": "Cebola Branca", "cat": "Hortifruti", "un": "KG", "code": "2002", "p": 5.40, "ncm": "07031011"},
        {"n": "Batata Inglesa Lavada", "cat": "Hortifruti", "un": "KG", "code": "2003", "p": 6.90, "ncm": "07019000"},
        {"n": "Banana Prata", "cat": "Hortifruti", "un": "KG", "code": "2004", "p": 5.80, "ncm": "08031000"},
        {"n": "Maçã Gala", "cat": "Hortifruti", "un": "KG", "code": "2005", "p": 12.50, "ncm": "08081000"},
        {"n": "Laranja Pera Rio", "cat": "Hortifruti", "un": "KG", "code": "2006", "p": 4.20, "ncm": "08051000"},

        # --- MERCEARIA / ALIMENTOS ---
        {"n": "Arroz Tio João Tipo 1 5kg", "cat": "Mercearia", "un": "PC", "code": "7891000053508", "p": 28.90, "ncm": "10063011"},
        {"n": "Feijão Carioca Kicaldo 1kg", "cat": "Mercearia", "un": "UN", "code": "7896010401115", "p": 8.45, "ncm": "07133399"},
        {"n": "Óleo de Soja Liza 900ml", "cat": "Mercearia", "un": "UN", "code": "7896036090126", "p": 7.20, "ncm": "15079011"},
        {"n": "Açúcar Refinado União 1kg", "cat": "Mercearia", "un": "UN", "code": "7896001700115", "p": 4.98, "ncm": "17019900"},
        {"n": "Café Pilão Tradicional 500g", "cat": "Mercearia", "un": "UN", "code": "7891095010011", "p": 18.90, "ncm": "09012100"},
        {"n": "Macarrão Galo Espaguete 500g", "cat": "Mercearia", "un": "UN", "code": "7891122000010", "p": 4.50, "ncm": "19021900"},
        {"n": "Leite UHT Paulista 1L", "cat": "Mercearia", "un": "UN", "code": "7896051111011", "p": 5.45, "ncm": "04012010"},

        # --- BEBIDAS ---
        {"n": "Coca-Cola Original 2L", "cat": "Bebidas", "un": "UN", "code": "7894900011517", "p": 9.98, "ncm": "22021000"},
        {"n": "Cerveja Skol Lata 350ml", "cat": "Bebidas", "un": "UN", "code": "7891149101110", "p": 3.49, "ncm": "22030000"},
        {"n": "Água Mineral Crystal 500ml", "cat": "Bebidas", "un": "UN", "code": "7894900010015", "p": 2.50, "ncm": "22011000"},
        {"n": "Suco Maguary Uva 1L", "cat": "Bebidas", "un": "UN", "code": "7896000508118", "p": 7.80, "ncm": "20096100"},

        # --- LIMPEZA ---
        {"n": "Detergente Ypê Coco 500ml", "cat": "Limpeza", "un": "UN", "code": "7896098900104", "p": 2.59, "ncm": "34022000"},
        {"n": "Sabão em Pó Omo 1.6kg", "cat": "Limpeza", "un": "PC", "code": "7891150011101", "p": 22.90, "ncm": "34022000"},
        {"n": "Amaciante Downy 500ml", "cat": "Limpeza", "un": "UN", "code": "7506195155110", "p": 15.90, "ncm": "38099190"},
        {"n": "Desinfetante Pinho Sol 1L", "cat": "Limpeza", "un": "UN", "code": "7891024131114", "p": 9.50, "ncm": "38089419"}
    ]

    @staticmethod
    def generate_cpf():
        """Gera CPF válido (Algoritmo Módulo 11) - MASTER REALISM"""
        cpf = [random.randint(0, 9) for _ in range(9)]
        for _ in range(2):
            val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
            cpf.append(11 - val if val > 1 else 0)
        return '%d%d%d.%d%d%d.%d%d%d-%d%d' % tuple(cpf)

    @classmethod
    def get_endereco_by_cep(cls, cep_limpo):
        """Busca endereço real via API (ViaCEP) com Cache Master - Magnitude Senior"""
        if cep_limpo in cls.CEP_CACHE:
            return cls.CEP_CACHE[cep_limpo]

        try:
            # Respeitar limites de API (sleep de 0.2s se não estiver em cache)
            time.sleep(0.2)
            r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if "erro" not in data:
                    res = {
                        "cep": data["cep"],
                        "logradouro": data["logradouro"],
                        "bairro": data["bairro"],
                        "cidade": data["localidade"],
                        "estado": data["uf"],
                        "numero": str(random.randint(1, 2000)),
                        "pais": "Brasil"
                    }
                    cls.CEP_CACHE[cep_limpo] = res
                    return res
        except Exception as e:
            print(f"Erro ao buscar CEP {cep_limpo}: {e}")
        
        # Fallback Master (Endereço Real de Manaus/SP se API falhar)
        return {
            "cep": "69005-000", "logradouro": "Av. Eduardo Ribeiro", "bairro": "Centro",
            "cidade": "Manaus", "estado": "AM", "numero": str(random.randint(1, 500)), "pais": "Brasil"
        }

    @classmethod
    def get_endereco_random(cls):
        """Retorna um endereço aleatório de uma lista de CEPs reais brasileiros"""
        ceps = ["69005000", "01001000", "20020010", "30140010", "40020000", "50030000"]
        return cls.get_endereco_by_cep(random.choice(ceps))

    @classmethod
    def inject_fornecedores(cls, estabelecimento_id, count=8):
        nomes = ["Friboi", "JBS Alimentos", "Seara Distribuição", "Ambev Manaus", "Nestlé BR", "Unilever Brasil"]
        objs = []
        for i, nome in enumerate(nomes[:count]):
            end = cls.get_endereco_random()
            forn = Fornecedor(
                estabelecimento_id=estabelecimento_id,
                nome_fantasia=f"{nome}",
                razao_social=f"{nome} Industrial S.A.",
                cnpj=f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
                telefone=f"(92) 3{random.randint(200,999)}-{random.randint(1000,9999)}",
                email=f"vendas@{nome.lower().replace(' ', '')}.com.br",
                **end
            )
            db.session.add(forn)
            objs.append(forn)
        db.session.commit()
        return objs

    @classmethod
    def inject_clientes(cls, estabelecimento_id, count=100):
        nomes = ["João Silva", "Maria Oliveira", "José Santos", "Ana Souza", "Carlos Pereira"]
        for i in range(count):
            end = cls.get_endereco_random()
            cli = Cliente(
                estabelecimento_id=estabelecimento_id,
                nome=f"{random.choice(nomes)} {uuid.uuid4().hex[:4].upper()}",
                cpf=cls.generate_cpf(),
                celular=f"(92) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}",
                limite_credito=random.choice([0, 500, 1000, 5000]),
                **end
            )
            db.session.add(cli)
        db.session.commit()

    @classmethod
    def inject_funcionarios_time(cls, estabelecimento_id, scenario_key=None):
        """Injeta time completo de funcionários com credenciais únicas (Magnitude Master)"""
        from app.models import Funcionario, Estabelecimento
        from werkzeug.security import generate_password_hash
        
        time_config = [
            {"c": "Gerente", "u": "admin", "n": "Gerente Geral"},
            {"c": "Caixa", "u": "caixa1", "n": "Operador de Caixa 01"},
            {"c": "Estoque", "u": "estoque1", "n": "Encarregado de Estoque"},
            {"c": "Auxiliar", "u": "aux1", "n": "Auxiliar Administrativo"}
        ]

        prefix = f"est{estabelecimento_id}_"
        
        scenario_map = {
            "ELITE": ("admin_elite", "adminElite123"),
            "BOM": ("admin_bom", "adminBom123"),
            "RAZOAVEL": ("admin_razoavel", "adminRazoavel123"),
            "MAL": ("admin_mal", "adminMal123"),
            "PESSIMO": ("admin_pessimo", "adminPessimo123")
        }

        funcionarios = []
        for config in time_config:
            if config['u'] == "admin" and scenario_key and scenario_key.upper() in scenario_map:
                username, senha_limpa = scenario_map[scenario_key.upper()]
            else:
                username = f"{prefix}{config['u']}" if config['u'] != "admin" else f"admin_{estabelecimento_id}"
                senha_limpa = f"{config['u']}123" if config['u'] != "admin" else f"admin{estabelecimento_id}"
            
            func = Funcionario.query.filter_by(username=username).first()
            if not func:
                end = cls.get_endereco_random()
                func = Funcionario(
                    estabelecimento_id=estabelecimento_id,
                    nome=f"{config['n']} - {estabelecimento_id}",
                    username=username,
                    cargo=config['c'],
                    role="ADMIN" if config['c'] == "Gerente" else "FUNCIONARIO",
                    cpf=cls.generate_cpf(),
                    email=f"{username}@mercadinhosys.com.br",
                    celular=f"(92) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}",
                    data_nascimento=date(1980 + random.randint(0,25), random.randint(1,12), random.randint(1,28)),
                    data_admissao=date.today() - timedelta(days=180),
                    ativo=True,
                    **end
                )
                db.session.add(func)
                func.set_password(senha_limpa)
                if config['c'] == "Gerente":
                    func.permissoes = {"pdv": True, "estoque": True, "compras": True, "financeiro": True, "configuracoes": True, "relatorios": True}
                funcionarios.append({"n": config['n'], "u": username, "s": senha_limpa, "c": config['c']})
        
        db.session.commit()
        return funcionarios

    @classmethod
    def inject_produtos_reais(cls, estabelecimento_id):
        """Injeta o MIX de produtos REAIS com Lotes, Validades e PEDIDOS DE COMPRA (Magnitude Master)"""
        # 1. Garantir Categorias
        cats = {}
        for cat_nome in set(p["cat"] for p in cls.SKU_DB):
            cat = CategoriaProduto.query.filter_by(estabelecimento_id=estabelecimento_id, nome=cat_nome).first()
            if not cat:
                cat = CategoriaProduto(estabelecimento_id=estabelecimento_id, nome=cat_nome)
                db.session.add(cat)
                db.session.commit()
            cats[cat_nome] = cat.id

        # 2. Obter dependências (Fornecedor e Funcionário ADMIN)
        fornecedores = Fornecedor.query.filter_by(estabelecimento_id=estabelecimento_id).all()
        if not fornecedores: return
        
        admin = Funcionario.query.filter_by(estabelecimento_id=estabelecimento_id, role="ADMIN").first()
        if not admin: return

        # 3. Criar Pedido de Compra Inicial (Para auditoria e estoque inicial)
        pedido = PedidoCompra(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=random.choice(fornecedores).id,
            funcionario_id=admin.id,
            numero_pedido=f"PEC-{uuid.uuid4().hex[:6].upper()}",
            data_pedido=date.today() - timedelta(days=60),
            data_recebimento=date.today() - timedelta(days=55),
            status="recebido",
            condicao_pagamento="30 DIAS",
            observacoes="Carga inicial de estoque via Simulation Engine"
        )
        db.session.add(pedido)
        db.session.flush()

        # 4. Injetar Produtos e Vincular ao Pedido
        total_pedido = Decimal("0.00")
        
        for item in cls.SKU_DB:
            p_venda = Decimal(str(item["p"] * random.uniform(0.9, 1.1)))
            p_custo = Decimal(str(p_venda / Decimal("1.4")))
            
            prod = Produto(
                estabelecimento_id=estabelecimento_id,
                categoria_id=cats[item["cat"]],
                fornecedor_id=pedido.fornecedor_id,
                nome=item["n"],
                codigo_barras=item.get("code"),
                codigo_interno=f"SKU-{uuid.uuid4().hex[:6].upper()}",
                unidade_medida=item["un"],
                ncm=item.get("ncm"),
                quantidade=0,
                preco_custo=p_custo,
                preco_venda=p_venda,
                ativo=True,
                margem_lucro=Decimal("40.0")
            )
            db.session.add(prod)
            db.session.flush()

            # Criar Item do Pedido
            qtd_inicial = cls.round_qty(random.uniform(50.0, 150.0))
            item_pedido = PedidoCompraItem(
                pedido_id=pedido.id,
                produto_id=prod.id,
                produto_nome=prod.nome,
                produto_unidade=prod.unidade_medida,
                quantidade_solicitada=qtd_inicial,
                quantidade_recebida=qtd_inicial,
                preco_unitario=p_custo,
                total_item=p_custo * qtd_inicial,
                status="recebido",
                estabelecimento_id=estabelecimento_id
            )
            db.session.add(item_pedido)
            total_pedido += item_pedido.total_item

            # Criar Lotes com Validade
            total_qty = Decimal("0.000")
            for l in range(2):
                data_fab = date.today() - timedelta(days=random.randint(60, 120))
                
                # Lógica MASTER de Validade Diversificada
                if l == 0: # Lote Mais Antigo
                    dias_val = random.randint(-5, 15) if item["cat"] in ["Açougue", "Hortifruti"] else random.randint(10, 45)
                else: # Lote Novo
                    dias_val = random.randint(30, 60) if item["cat"] in ["Açougue", "Hortifruti"] else random.randint(180, 365)
                
                data_val = date.today() + timedelta(days=dias_val)
                
                qtd_lote = cls.round_qty(qtd_inicial / 2)
                lote = ProdutoLote(
                    estabelecimento_id=estabelecimento_id,
                    produto_id=prod.id,
                    fornecedor_id=pedido.fornecedor_id,
                    pedido_compra_id=pedido.id,
                    numero_lote=f"LT-{uuid.uuid4().hex[:8].upper()}",
                    quantidade=qtd_lote,
                    quantidade_inicial=qtd_lote,
                    data_fabricacao=data_fab,
                    data_validade=data_val,
                    data_entrada=date.today() - timedelta(days=55),
                    preco_custo_unitario=p_custo,
                    ativo=True
                )
                db.session.add(lote)
                total_qty += qtd_lote
            
            prod.quantidade = cls.round_qty(total_qty)
            prod.quantidade_minima = cls.round_qty("15.0")
            prod.controlar_validade = True
            
            # Sincroniza informações do lote principal (FIFO) no Produto
            lote_principal = ProdutoLote.query.filter_by(produto_id=prod.id).order_by(ProdutoLote.data_validade.asc()).first()
            if lote_principal:
                prod.lote = lote_principal.numero_lote
                prod.data_validade = lote_principal.data_validade
                prod.data_fabricacao = lote_principal.data_fabricacao

        pedido.subtotal = total_pedido
        pedido.total = total_pedido
        db.session.commit()
        print(f"✅ MAGNITUDE MASTER: {len(cls.SKU_DB)} SKUs ativos vinculados a Pedido de Compra #{pedido.numero_pedido}")
