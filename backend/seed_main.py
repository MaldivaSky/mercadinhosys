#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_main.py – Seed PROFISSIONAL para MercadinhoSys
=====================================================
- Baseado inteiramente nos models.py reais (campos, nullable, UniqueConstraints)
- Commits em batches de 100 vendas + sleep para não sobrecarregar o Aiven
- Lotes em memória (sem N+1 queries ao banco por venda)
- Todos os UniqueConstraints respeitados com contadores sequenciais por est

UniqueConstraints mapeados do models.py:
  Estabelecimento   → cnpj
  Funcionario       → nenhum global (username livre por não ter UK definido)
  BancoHoras        → (funcionario_id, mes_referencia)  [uq_banco_func_mes]
  Cliente           → (estabelecimento_id, cpf)          [uq_cliente_estab_cpf]
  Fornecedor        → (estabelecimento_id, cnpj)         [uq_fornecedor_estab_cnpj]
  CategoriaProduto  → (estabelecimento_id, codigo)       [uq_cat_estab_codigo]
  Produto           → (estabelecimento_id, codigo_interno) [uq_produto_estab_codigo]
  ProdutoLote       → (estabelecimento_id, numero_lote)  [uq_lote_estab_numero]
  PedidoCompra      → (estabelecimento_id, numero_pedido) [uq_pedido_estab_numero]
  Venda             → (estabelecimento_id, codigo)       [uq_venda_estab_codigo]
"""

import sys
import os
import time
import random
import json
from datetime import datetime, date, timedelta, time as dtime
from decimal import Decimal, ROUND_HALF_UP

# Ajuste de path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Encoding Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from faker import Faker
fake = Faker('pt_BR')

from app import create_app
from app.models import (
    db, Estabelecimento, Configuracao, Funcionario, Beneficio,
    FuncionarioBeneficio, BancoHoras, JustificativaPonto, RegistroPonto,
    ConfiguracaoHorario, Fornecedor, CategoriaProduto, Produto, ProdutoLote,
    Cliente, PedidoCompra, PedidoCompraItem, Venda, VendaItem,
    MovimentacaoEstoque, HistoricoPrecos, ContaPagar, ContaReceber, Despesa,
    Caixa, MovimentacaoCaixa, LoginHistory, RelatorioAgendado, DashboardMetrica
)

# ==================== CONFIGURAÇÕES GLOBAIS ====================
TODAY = date.today()
NOW   = datetime.utcnow()
START_DATE  = TODAY - timedelta(days=180)
PONTO_START = TODAY - timedelta(days=30)

# Tamanho do batch de vendas para não sobrecarregar o Aiven
VENDA_BATCH = 100
VENDA_SLEEP = 2  # segundos de sleep entre batches

# ==================== DADOS REAIS ====================

CATEGORIAS = [
    "Bebidas", "Laticínios", "Mercearia", "Limpeza", "Higiene Pessoal",
    "Hortifrúti", "Carnes", "Padaria", "Congelados", "Pet Shop"
]

# (nome, marca, categoria, custo, venda)
PRODUTOS_REAIS = [
    # Mercearia
    ("Arroz Branco Tipo 1 5kg", "Camil", "Mercearia", 20.00, 29.90),
    ("Arroz Integral 5kg", "Tio João", "Mercearia", 18.00, 26.90),
    ("Feijão Carioca 1kg", "Camil", "Mercearia", 7.50, 11.90),
    ("Feijão Preto 1kg", "Kicaldo", "Mercearia", 8.00, 12.90),
    ("Óleo de Soja 900ml", "Soya", "Mercearia", 5.00, 7.99),
    ("Açúcar Refinado 1kg", "União", "Mercearia", 3.50, 5.49),
    ("Açúcar Mascavo 1kg", "Native", "Mercearia", 4.00, 6.90),
    ("Sal Refinado 1kg", "Cisne", "Mercearia", 1.80, 2.99),
    ("Café Torrado Moído 500g", "Pilão", "Mercearia", 12.00, 18.90),
    ("Café em Pó 500g", "Três Corações", "Mercearia", 11.50, 17.90),
    ("Farinha de Trigo 1kg", "Dona Benta", "Mercearia", 3.20, 5.49),
    ("Farinha de Mandioca 500g", "Yoki", "Mercearia", 4.50, 7.90),
    ("Macarrão Espaguete 500g", "Adria", "Mercearia", 2.80, 4.49),
    ("Macarrão Penne 500g", "Barilla", "Mercearia", 4.50, 7.90),
    ("Molho de Tomate 340g", "Pomarola", "Mercearia", 2.50, 4.29),
    ("Extrato de Tomate 130g", "Elefante", "Mercearia", 3.00, 5.49),
    ("Ervilha em Lata 170g", "Hemmer", "Mercearia", 3.20, 5.79),
    ("Milho em Lata 200g", "Hemmer", "Mercearia", 3.20, 5.79),
    ("Sardinha em Lata 125g", "Gomes da Costa", "Mercearia", 4.50, 7.99),
    ("Atum Ralado 170g", "Gomes da Costa", "Mercearia", 5.00, 8.90),
    # Laticínios
    ("Leite UHT Integral 1L", "Italac", "Laticínios", 3.50, 5.49),
    ("Leite UHT Desnatado 1L", "Italac", "Laticínios", 3.50, 5.49),
    ("Leite em Pó Integral 400g", "Ninho", "Laticínios", 15.00, 24.90),
    ("Iogurte Natural 170g", "Nestlé", "Laticínios", 2.50, 4.49),
    ("Iogurte de Morango 170g", "Vigor", "Laticínios", 2.80, 4.99),
    ("Queijo Muçarela Fatiado 150g", "Président", "Laticínios", 12.00, 19.90),
    ("Queijo Prato Fatiado 150g", "Président", "Laticínios", 13.00, 20.90),
    ("Requeijão Cremoso 250g", "Vigor", "Laticínios", 5.00, 8.49),
    ("Manteiga com Sal 200g", "Aviação", "Laticínios", 7.00, 11.90),
    ("Margarina 500g", "Qualy", "Laticínios", 4.00, 6.99),
    ("Creme de Leite 200g", "Nestlé", "Laticínios", 3.00, 5.29),
    ("Leite Condensado 395g", "Moça", "Laticínios", 4.50, 7.49),
    # Bebidas
    ("Coca-Cola 2L", "Coca-Cola", "Bebidas", 6.00, 9.99),
    ("Guaraná Antarctica 2L", "Antarctica", "Bebidas", 5.00, 8.49),
    ("Pepsi 2L", "Pepsi", "Bebidas", 5.00, 8.49),
    ("Suco de Laranja Del Valle 1L", "Del Valle", "Bebidas", 4.00, 6.99),
    ("Suco de Uva Del Valle 1L", "Del Valle", "Bebidas", 4.50, 7.49),
    ("Água Mineral Crystal 500ml", "Crystal", "Bebidas", 1.20, 2.49),
    ("Água Mineral Crystal 1.5L", "Crystal", "Bebidas", 2.00, 3.99),
    ("Cerveja Skol 350ml Lata", "Skol", "Bebidas", 2.50, 4.29),
    ("Cerveja Brahma 350ml Lata", "Brahma", "Bebidas", 2.50, 4.29),
    ("Cerveja Colorado IPA 355ml", "Colorado", "Bebidas", 5.00, 8.99),
    ("Vinho Tinto Gato Negro 750ml", "Gato Negro", "Bebidas", 25.00, 39.90),
    ("Vinho Branco Casillero 750ml", "Casillero del Diablo", "Bebidas", 40.00, 59.90),
    # Limpeza
    ("Sabão em Pó Omo 1kg", "Omo", "Limpeza", 12.00, 19.90),
    ("Sabão em Pó Ariel 1kg", "Ariel", "Limpeza", 13.00, 21.90),
    ("Amaciante Downy 1L", "Downy", "Limpeza", 10.00, 16.90),
    ("Detergente Ypê 500ml", "Ypê", "Limpeza", 1.80, 2.99),
    ("Detergente Limpol 500ml", "Limpol", "Limpeza", 1.60, 2.79),
    ("Água Sanitária Q-Boa 1L", "Q-Boa", "Limpeza", 3.00, 5.49),
    ("Desinfetante Pinho Sol 500ml", "Pinho Sol", "Limpeza", 4.00, 6.99),
    ("Palha de Aço Bombril c/8", "Bombril", "Limpeza", 1.00, 1.99),
    ("Esponja Scotch-Brite Dupla", "Scotch-Brite", "Limpeza", 2.50, 4.49),
    ("Limpador Veja Multiuso 500ml", "Veja", "Limpeza", 4.00, 6.99),
    # Higiene Pessoal
    ("Papel Higiênico Neve 12 rolos", "Neve", "Higiene Pessoal", 12.00, 19.90),
    ("Papel Higiênico Personal 12 rolos", "Personal", "Higiene Pessoal", 13.00, 21.90),
    ("Shampoo Seda 325ml", "Seda", "Higiene Pessoal", 8.00, 13.90),
    ("Condicionador Seda 325ml", "Seda", "Higiene Pessoal", 8.00, 13.90),
    ("Sabonete Dove 90g", "Dove", "Higiene Pessoal", 2.00, 3.49),
    ("Sabonete Líquido Protex 250ml", "Protex", "Higiene Pessoal", 5.00, 8.90),
    ("Creme Dental Colgate 90g", "Colgate", "Higiene Pessoal", 3.00, 5.49),
    ("Creme Dental Sorriso 90g", "Sorriso", "Higiene Pessoal", 2.50, 4.49),
    ("Desodorante Rexona Aerosol 150ml", "Rexona", "Higiene Pessoal", 10.00, 16.90),
    ("Desodorante Dove Roll-on 50ml", "Dove", "Higiene Pessoal", 8.00, 13.90),
    ("Fralda Pampers P c/22", "Pampers", "Higiene Pessoal", 35.00, 54.90),
    ("Fralda Pampers M c/20", "Pampers", "Higiene Pessoal", 36.00, 55.90),
    ("Absorvente Always Noturno c/8", "Always", "Higiene Pessoal", 8.00, 13.90),
    ("Cotonete Johnson's c/75", "Johnson's", "Higiene Pessoal", 5.00, 8.90),
    # Hortifrúti
    ("Batata Inglesa 1kg", "In natura", "Hortifrúti", 3.00, 5.99),
    ("Cebola 1kg", "In natura", "Hortifrúti", 4.00, 7.49),
    ("Tomate 1kg", "In natura", "Hortifrúti", 5.00, 8.99),
    ("Alface Crespa unid.", "In natura", "Hortifrúti", 2.00, 3.99),
    ("Banana Prata 1kg", "In natura", "Hortifrúti", 4.00, 6.99),
    ("Maçã Fuji 1kg", "In natura", "Hortifrúti", 6.00, 9.99),
    ("Laranja Pera 1kg", "In natura", "Hortifrúti", 3.00, 5.49),
    ("Limão Taiti 1kg", "In natura", "Hortifrúti", 3.50, 5.99),
    # Carnes
    ("Peito de Frango Sadia 1kg", "Sadia", "Carnes", 14.00, 22.90),
    ("Coxa e Sobrecoxa Sadia 1kg", "Sadia", "Carnes", 10.00, 16.90),
    ("Carne Moída Friboi 500g", "Friboi", "Carnes", 12.00, 19.90),
    ("Alcatra Friboi 1kg", "Friboi", "Carnes", 35.00, 54.90),
    ("Contrafilé Friboi 1kg", "Friboi", "Carnes", 38.00, 59.90),
    ("Linguiça Toscana Aurora 500g", "Aurora", "Carnes", 15.00, 24.90),
    ("Hambúrguer Sadia 672g", "Sadia", "Carnes", 12.00, 19.90),
    # Congelados
    ("Pizza Margherita Forno de Minas 460g", "Forno de Minas", "Congelados", 15.00, 24.90),
    ("Sorvete Kibon 1.5L", "Kibon", "Congelados", 18.00, 29.90),
    ("Batata Palito McCain 400g", "McCain", "Congelados", 12.00, 19.90),
    ("Lasanha Sadia 600g", "Sadia", "Congelados", 14.00, 22.90),
    # Padaria
    ("Pão de Forma Pullman 500g", "Pullman", "Padaria", 5.00, 8.49),
    ("Biscoito Cream Cracker Tostines 200g", "Tostines", "Padaria", 3.00, 5.29),
    ("Biscoito Recheado Trakinas 126g", "Trakinas", "Padaria", 2.50, 4.49),
    ("Bolo de Chocolate Ana Maria 270g", "Ana Maria", "Padaria", 4.00, 6.99),
    # Pet Shop
    ("Ração Pedigree Cães Adultos 10kg", "Pedigree", "Pet Shop", 60.00, 99.90),
    ("Ração Whiskas Gatos 5kg", "Whiskas", "Pet Shop", 40.00, 69.90),
]

FORNECEDORES_REAIS = [
    "Camil Alimentos", "JBS / Friboi", "Sadia / BRF", "Nestlé Brasil",
    "Coca-Cola FEMSA", "Ambev", "Unilever Brasil", "P&G Brasil",
    "Kimberly-Clark", "Ypê Indústrias", "Bombril", "Johnson & Johnson",
    "Colgate-Palmolive", "Seara Alimentos", "Aurora Alimentos",
    "Italac Alimentos", "Vigor Alimentos", "Président Lactalis",
    "Pedigree / Mars", "Whiskas / Mars",
]

NOMES_CLIENTES = [
    "João da Silva", "Maria Santos", "José Oliveira", "Ana Souza", "Carlos Lima",
    "Fernanda Rocha", "Antônio Alves", "Mariana Costa", "Paulo Pereira",
    "Patrícia Ferreira", "Ricardo Martins", "Camila Rodrigues", "Lucas Nunes",
    "Juliana Mendes", "Pedro Carvalho", "Amanda Ribeiro", "Bruno Teixeira",
    "Larissa Gomes", "Daniel Barbosa", "Natália Dias", "Rafael Cardoso",
    "Bianca Monteiro", "Marcelo Barros", "Luciana Freitas", "Felipe Azevedo",
    "Vanessa Correia", "Gustavo Cunha", "Tatiana Fogaça", "Leonardo Viana",
    "Sabrina Duarte",
]

# ==================== FUNÇÕES AUXILIARES ====================

def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_datetime(start: date, end: date) -> datetime:
    d = random_date(start, end)
    h = random.randint(8, 21)
    m = random.choice([0, 10, 20, 30, 40, 50])
    return datetime(d.year, d.month, d.day, h, m, 0)

def random_time(start_hour=8, end_hour=18):
    return dtime(random.randint(start_hour, end_hour), random.choice([0, 15, 30, 45]))

def fmt(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# ==================== SEED PRINCIPAL ====================

def seed(app):
    with app.app_context():
        print("🚀 Iniciando seed PROFISSIONAL para MercadinhoSys...")
        db.drop_all()
        db.create_all()
        print("✅ Banco recriado com sucesso.")

        # Contadores sequenciais por estabelecimento (garantem unicidade)
        seq = {}  # est_id → dict de contadores

        def next_seq(est_id, key):
            seq[est_id][key] += 1
            return seq[est_id][key]

        # -------------------------------------------------------
        # 1. ESTABELECIMENTOS
        # -------------------------------------------------------
        print("🏪 Criando estabelecimentos...")
        est1 = Estabelecimento(
            nome_fantasia="Mercadinho Maldivas",
            razao_social="Maldivas Shopp Ltda",
            cnpj="12.345.678/0001-99",
            inscricao_estadual="123456789",
            telefone="(21) 98888-0001",
            email="rafaelmaldivas@gmail.com",
            cep="20041-008",
            logradouro="Rua da Carioca",
            numero="100",
            bairro="Centro",
            cidade="Rio de Janeiro",
            estado="RJ",
            pais="Brasil",
            ativo=True,
            regime_tributario="SIMPLES NACIONAL",
            data_abertura=date(2020, 1, 1),
            plano="Premium",
            plano_status="ativo",
        )
        db.session.add(est1)

        est2 = Estabelecimento(
            nome_fantasia="Supermercado Praia",
            razao_social="Praia Comércio de Alimentos Ltda",
            cnpj="98.765.432/0001-11",
            inscricao_estadual="987654321",
            telefone="(21) 98888-0002",
            email="contato@superpraia.com.br",
            cep="22010-010",
            logradouro="Av. Atlântica",
            numero="2000",
            bairro="Copacabana",
            cidade="Rio de Janeiro",
            estado="RJ",
            pais="Brasil",
            ativo=True,
            regime_tributario="LUCRO PRESUMIDO",
            data_abertura=date(2019, 5, 10),
            plano="Advanced",
            plano_status="ativo",
        )
        db.session.add(est2)
        db.session.flush()

        estabelecimentos = [est1, est2]

        for est in estabelecimentos:
            seq[est.id] = {
                "lote": 0, "pedido": 0, "venda": 0, "prod": 0
            }
            cfg = Configuracao(
                estabelecimento_id=est.id,
                formas_pagamento=json.dumps(["Dinheiro", "Pix", "Cartão de Crédito",
                                             "Cartão de Débito", "Fiado"]),
                logo_url="https://via.placeholder.com/200x100?text=Logo",
                controlar_validade=True,
                alerta_estoque_minimo=True,
                permitir_venda_sem_estoque=False,
            )
            db.session.add(cfg)
        db.session.flush()

        # -------------------------------------------------------
        # 2. FUNCIONÁRIOS (5 por estabelecimento, usernames únicos)
        # -------------------------------------------------------
        print("👥 Criando funcionários...")
        funcionarios = []

        FUNC_TEMPLATES = [
            # (nome, username_prefix, role, cargo, salario)
            ("Rafael Maldivas",   "admin",    "ADMIN",      "Proprietário",         5000.00),
            ("Ana Paula Caixa",   "caixa",    "CAIXA",      "Operador de Caixa",    1850.00),
            ("Pedro Estoque",     "estoque",  "FUNCIONARIO","Auxiliar de Estoque",  1700.00),
            ("Mariana Auxiliar",  "auxiliar", "FUNCIONARIO","Auxiliar Administrativo", 1900.00),
            ("João Repositor",    "repositor","FUNCIONARIO","Repositor",             1600.00),
        ]
        SENHAS = {
            "ADMIN": "admin123", "CAIXA": "caixa123", "FUNCIONARIO": "func123"
        }

        for est_idx, est in enumerate(estabelecimentos):
            for t_nome, t_user, t_role, t_cargo, t_sal in FUNC_TEMPLATES:
                f = Funcionario(
                    estabelecimento_id=est.id,
                    nome=t_nome,
                    username=t_user if est_idx == 0 else f"{t_user}2",
                    role=t_role,
                    cargo=t_cargo,
                    salario_base=t_sal,
                    cpf=fake.cpf(),
                    rg=fake.rg(),
                    data_nascimento=fake.date_of_birth(minimum_age=22, maximum_age=55),
                    celular=fake.cellphone_number(),
                    email=f"{t_user}@mercadinho.com" if est_idx == 0 else f"{t_user}2@mercadinho.com",
                    data_admissao=random_date(date(2020, 1, 1), TODAY - timedelta(days=60)),
                    ativo=True,
                    cep=est.cep,
                    logradouro=est.logradouro,
                    numero=str(random.randint(10, 999)),
                    bairro=est.bairro,
                    cidade=est.cidade,
                    estado=est.estado,
                    permissoes_json=json.dumps({
                        "pdv": t_role in ("ADMIN", "CAIXA"),
                        "estoque": t_role in ("ADMIN", "FUNCIONARIO"),
                        "compras": t_role == "ADMIN",
                        "financeiro": t_role == "ADMIN",
                        "configuracoes": t_role == "ADMIN",
                    }),
                )
                f.set_senha(SENHAS[t_role])
                db.session.add(f)
                funcionarios.append(f)
        db.session.flush()

        # -------------------------------------------------------
        # 3. BENEFÍCIOS (por estabelecimento)
        # -------------------------------------------------------
        print("🎁 Criando benefícios...")
        beneficios = []
        for est in estabelecimentos:
            for nome_b, desc_b, val_b in [
                ("Vale Alimentação", "Cartão alimentação mensal", 450.00),
                ("Vale Transporte",  "Passe mensal de transporte", 220.00),
                ("Plano de Saúde",   "Coparticipação no plano", 150.00),
            ]:
                b = Beneficio(
                    estabelecimento_id=est.id,
                    nome=nome_b, descricao=desc_b, valor_padrao=val_b, ativo=True
                )
                db.session.add(b)
                beneficios.append(b)
        db.session.flush()

        # Associar benefícios apenas a funcionários do mesmo estabelecimento
        for func in funcionarios:
            if func.ativo:
                for b in [x for x in beneficios if x.estabelecimento_id == func.estabelecimento_id]:
                    db.session.add(FuncionarioBeneficio(
                        funcionario_id=func.id,
                        beneficio_id=b.id,
                        valor=b.valor_padrao,
                        ativo=True,
                    ))
        db.session.flush()

        # -------------------------------------------------------
        # 4. FORNECEDORES (10 por estabelecimento, CNPJ único por est)
        # -------------------------------------------------------
        print("🏭 Criando fornecedores...")
        fornecedores = []
        cnpjs_usados = set()

        for est in estabelecimentos:
            nomes_para_est = random.sample(FORNECEDORES_REAIS, 10)
            for nome_f in nomes_para_est:
                cnpj = fake.cnpj()
                while cnpj in cnpjs_usados:
                    cnpj = fake.cnpj()
                cnpjs_usados.add(cnpj)
                fn = Fornecedor(
                    estabelecimento_id=est.id,
                    nome_fantasia=nome_f,
                    razao_social=f"{nome_f} Ltda",
                    cnpj=cnpj,
                    inscricao_estadual=fake.estado_sigla() + str(random.randint(10000000, 99999999)),
                    telefone=fake.phone_number(),
                    email=f"comercial@{nome_f.split()[0].lower()}{random.randint(1,99)}.com.br",
                    cep=fake.postcode(),
                    logradouro=fake.street_name(),
                    numero=str(random.randint(1, 999)),
                    bairro=fake.bairro(),
                    cidade=fake.city(),
                    estado=fake.estado_sigla(),
                    ativo=True,
                )
                db.session.add(fn)
                fornecedores.append(fn)
        db.session.flush()

        # -------------------------------------------------------
        # 5. CATEGORIAS (código único por est via sequencial)
        # -------------------------------------------------------
        print("🏷️ Criando categorias...")
        categorias_por_est = {}
        cat_cod_seq = {}  # est_id → int

        for est in estabelecimentos:
            cat_dict = {}
            cat_cod_seq[est.id] = 0
            for nome_cat in CATEGORIAS:
                cat_cod_seq[est.id] += 1
                cat = CategoriaProduto(
                    estabelecimento_id=est.id,
                    nome=nome_cat,
                    codigo=f"CAT{est.id:02d}{cat_cod_seq[est.id]:03d}",
                    ativo=True,
                )
                db.session.add(cat)
                db.session.flush()
                cat_dict[nome_cat] = cat
            categorias_por_est[est.id] = cat_dict
        db.session.flush()

        # -------------------------------------------------------
        # 6. PRODUTOS + LOTES (em memória: produto_id → lista de lotes)
        # -------------------------------------------------------
        print(f"📦 Criando {len(PRODUTOS_REAIS)} produtos realistas...")
        produtos_por_est = {est.id: [] for est in estabelecimentos}

        # Mapa em memória para FIFO sem queries: produto_id → [{"qtd": x, "validade": date}]
        lotes_mem: dict[int, list] = {}

        for nome_p, marca_p, cat_nome, custo_p, venda_p in PRODUTOS_REAIS:
            est = random.choice(estabelecimentos)
            cat = categorias_por_est[est.id][cat_nome]
            fns_est = [f for f in fornecedores if f.estabelecimento_id == est.id]
            fornecedor = random.choice(fns_est)

            idx_p = next_seq(est.id, "prod")
            cod_int = f"{cat_nome[:2].upper()}{est.id:02d}{idx_p:04d}"

            prod = Produto(
                estabelecimento_id=est.id,
                categoria_id=cat.id,
                fornecedor_id=fornecedor.id,
                nome=nome_p,
                codigo_interno=cod_int,
                preco_custo=fmt(custo_p),
                preco_venda=fmt(venda_p),
                quantidade=0,
                quantidade_minima=random.randint(5, 20),
                unidade_medida="UN",
                ncm=fake.numerify(text="########"),
                marca=marca_p,
                fabricante=marca_p,
                tipo=cat_nome,
                subcategoria="Geral",
                ativo=True,
                imagem_url=f"https://via.placeholder.com/300x300?text={nome_p[:20].replace(' ', '+')}",
                controlar_validade=True,
            )
            db.session.add(prod)
            db.session.flush()
            produtos_por_est[est.id].append(prod)
            lotes_mem[prod.id] = []

            # 2 lotes por produto (número único por est)
            for _ in range(2):
                data_entrada = random_date(START_DATE - timedelta(days=60), TODAY - timedelta(days=1))
                data_val = data_entrada + timedelta(days=random.randint(60, 365))
                qtd_ini = random.randint(80, 250)
                num_lote = f"LOT{est.id:02d}{next_seq(est.id, 'lote'):06d}"
                lote = ProdutoLote(
                    estabelecimento_id=est.id,
                    produto_id=prod.id,
                    fornecedor_id=fornecedor.id,
                    numero_lote=num_lote,
                    quantidade=qtd_ini,
                    quantidade_inicial=qtd_ini,
                    data_entrada=data_entrada,
                    data_validade=data_val,
                    preco_custo_unitario=prod.preco_custo,
                    ativo=True,
                )
                db.session.add(lote)
                prod.quantidade += qtd_ini
                # Registrar em memória (ordenado por validade para FIFO)
                lotes_mem[prod.id].append({"obj": lote, "validade": data_val})
            # Ordenar por validade ASC (FIFO)
            lotes_mem[prod.id].sort(key=lambda x: x["validade"])

        db.session.flush()

        # -------------------------------------------------------
        # 7. CLIENTES (CPF único por estabelecimento)
        # -------------------------------------------------------
        print("👤 Criando 30 clientes...")
        clientes = []
        cpfs_usados = set()

        for nome_cli in NOMES_CLIENTES:
            est = random.choice(estabelecimentos)
            cpf = fake.cpf()
            for _ in range(30):
                if cpf not in cpfs_usados:
                    break
                cpf = fake.cpf()
            cpfs_usados.add(cpf)
            cli = Cliente(
                estabelecimento_id=est.id,
                nome=nome_cli,
                cpf=cpf,
                rg=fake.rg(),
                data_nascimento=fake.date_of_birth(minimum_age=18, maximum_age=80),
                telefone=fake.phone_number(),
                celular=fake.cellphone_number(),
                email=fake.email(),
                cep=fake.postcode(),
                logradouro=fake.street_name(),
                numero=str(random.randint(1, 999)),
                bairro=fake.bairro(),
                cidade=fake.city(),
                estado=fake.estado_sigla(),
                ativo=True,
                limite_credito=fmt(random.uniform(200, 2000)),
            )
            db.session.add(cli)
            clientes.append(cli)
        db.session.flush()

        # -------------------------------------------------------
        # 8. PEDIDOS DE COMPRA (1 por produto, número único por est)
        # -------------------------------------------------------
        print("📋 Gerando pedidos de compra...")
        pedidos_compra = []

        for est in estabelecimentos:
            funcs_est = [f for f in funcionarios if f.estabelecimento_id == est.id]
            fns_est   = [f for f in fornecedores if f.estabelecimento_id == est.id]

            for produto in produtos_por_est[est.id]:
                data_ped = random_date(START_DATE - timedelta(days=30), TODAY - timedelta(days=1))
                fornecedor = random.choice(fns_est)
                num_pc = f"PC{est.id:02d}-{next_seq(est.id, 'pedido'):05d}"

                pc = PedidoCompra(
                    estabelecimento_id=est.id,
                    fornecedor_id=fornecedor.id,
                    funcionario_id=random.choice(funcs_est).id,
                    numero_pedido=num_pc,
                    data_pedido=datetime.combine(data_ped, dtime(10, 0)),
                    data_recebimento=data_ped + timedelta(days=random.randint(1, 7)),
                    status="recebido",
                    subtotal=0,
                    desconto=0,
                    frete=0,
                    total=0,
                )
                db.session.add(pc)
                db.session.flush()
                pedidos_compra.append(pc)

                qtd_sol = random.randint(50, 200)
                preco_u = produto.preco_custo
                total_it = float(preco_u) * qtd_sol

                db.session.add(PedidoCompraItem(
                    pedido_id=pc.id,
                    produto_id=produto.id,
                    produto_nome=produto.nome,
                    produto_unidade="UN",
                    quantidade_solicitada=qtd_sol,
                    quantidade_recebida=qtd_sol,
                    preco_unitario=preco_u,
                    total_item=total_it,
                    status="recebido",
                ))

                # Adicionar ao lote existente (sem criar novo)
                lotes_prod = ProdutoLote.query.filter_by(produto_id=produto.id).all()
                if lotes_prod:
                    lotes_prod[0].quantidade += qtd_sol
                    if produto.id in lotes_mem and lotes_mem[produto.id]:
                        lotes_mem[produto.id][0]["obj"].quantidade += qtd_sol

                produto.quantidade += qtd_sol
                pc.subtotal = total_it
                pc.total = total_it

                db.session.add(MovimentacaoEstoque(
                    estabelecimento_id=est.id,
                    produto_id=produto.id,
                    pedido_compra_id=pc.id,
                    funcionario_id=pc.funcionario_id,
                    tipo="entrada",
                    quantidade=qtd_sol,
                    quantidade_anterior=produto.quantidade - qtd_sol,
                    quantidade_atual=produto.quantidade,
                    custo_unitario=preco_u,
                    valor_total=total_it,
                    motivo="Compra",
                ))

        db.session.commit()
        print("   ✅ Pedidos de compra commitados.")

        # -------------------------------------------------------
        # 9. VENDAS — em batches de 100 com sleep entre batches
        # -------------------------------------------------------
        print(f"💰 Gerando 1800 vendas em batches de {VENDA_BATCH} (sleep {VENDA_SLEEP}s)...")

        vendas_geradas = []
        funcionarios_ativos_por_est = {
            est.id: [f for f in funcionarios if f.estabelecimento_id == est.id and f.ativo]
            for est in estabelecimentos
        }
        clientes_por_est = {}
        for cli in clientes:
            clientes_por_est.setdefault(cli.estabelecimento_id, []).append(cli)

        FORMAS = ["Dinheiro", "Pix", "Cartão de Crédito", "Cartão de Débito", "Fiado"]
        PESOS  = [40, 30, 15, 10, 5]

        num_vendas_alvo = 1800
        vendas_criadas  = 0
        tentativas      = 0
        batch_atual     = []

        def consumir_mem(prod_id, quantidade_desejada):
            """FIFO em memória: consume dos lotes mais antigos primeiro."""
            lotes = lotes_mem.get(prod_id, [])
            restante = quantidade_desejada
            consumido = 0
            for lote_info in lotes:
                if restante <= 0:
                    break
                disp = lote_info["obj"].quantidade
                usar = min(restante, disp)
                if usar > 0:
                    lote_info["obj"].quantidade -= usar
                    restante -= usar
                    consumido += usar
            return consumido

        while vendas_criadas < num_vendas_alvo and tentativas < num_vendas_alvo * 3:
            tentativas += 1
            est = random.choice(estabelecimentos)
            data_venda = random_datetime(START_DATE, TODAY - timedelta(days=1))
            funcionario = random.choice(funcionarios_ativos_por_est[est.id])
            cli_list = clientes_por_est.get(est.id, [])
            cliente = random.choice(cli_list) if cli_list and random.random() < 0.7 else None
            forma_pag = random.choices(FORMAS, weights=PESOS)[0]

            prod_com_estoque = [p for p in produtos_por_est[est.id] if p.quantidade > 0]
            if not prod_com_estoque:
                continue

            num_itens = random.randint(1, min(6, len(prod_com_estoque)))
            prods_sel = random.sample(prod_com_estoque, num_itens)
            itens_venda = []
            total_venda = 0.0

            for prod in prods_sel:
                qtd_desej = random.randint(1, 4)
                qtd_cons  = consumir_mem(prod.id, qtd_desej)
                if qtd_cons == 0:
                    continue
                preco = float(prod.preco_venda)
                t_item = preco * qtd_cons
                itens_venda.append((prod, qtd_cons, preco, t_item))
                total_venda += t_item
                prod.quantidade -= qtd_cons

            if not itens_venda:
                continue

            cod_venda = f"V{est.id:02d}-{next_seq(est.id, 'venda'):07d}"
            venda = Venda(
                estabelecimento_id=est.id,
                cliente_id=cliente.id if cliente else None,
                funcionario_id=funcionario.id,
                codigo=cod_venda,
                data_venda=data_venda,
                status="finalizada",
                forma_pagamento=forma_pag,
                subtotal=fmt(total_venda),
                desconto=0,
                total=fmt(total_venda),
                valor_recebido=fmt(total_venda),
                troco=0,
                quantidade_itens=len(itens_venda),
            )
            db.session.add(venda)
            db.session.flush()

            for prod, qtd, preco, t_item in itens_venda:
                db.session.add(VendaItem(
                    venda_id=venda.id,
                    produto_id=prod.id,
                    produto_nome=prod.nome,
                    produto_codigo=prod.codigo_interno,
                    produto_unidade="UN",
                    quantidade=qtd,
                    preco_unitario=fmt(preco),
                    desconto=0,
                    total_item=fmt(t_item),
                    custo_unitario=prod.preco_custo,
                    margem_lucro_real=fmt((preco - float(prod.preco_custo)) * qtd),
                ))
                db.session.add(MovimentacaoEstoque(
                    estabelecimento_id=est.id,
                    produto_id=prod.id,
                    venda_id=venda.id,
                    funcionario_id=funcionario.id,
                    tipo="saida",
                    quantidade=qtd,
                    quantidade_anterior=prod.quantidade + qtd,
                    quantidade_atual=prod.quantidade,
                    custo_unitario=prod.preco_custo,
                    valor_total=fmt(t_item),
                    motivo="Venda",
                ))

            # Conta a receber se Fiado
            if forma_pag == "Fiado" and cliente:
                data_venc = (data_venda + timedelta(days=30)).date()
                pago = random.random() < 0.6
                db.session.add(ContaReceber(
                    estabelecimento_id=est.id,
                    cliente_id=cliente.id,
                    venda_id=venda.id,
                    numero_documento=f"CR-{cod_venda}",
                    valor_original=fmt(total_venda),
                    valor_recebido=fmt(total_venda) if pago else fmt(0),
                    valor_atual=fmt(0) if pago else fmt(total_venda),
                    data_emissao=data_venda.date(),
                    data_vencimento=data_venc,
                    data_recebimento=data_venc if pago else None,
                    status="pago" if pago else "aberto",
                ))

            batch_atual.append(venda)
            vendas_criadas += 1

            # Commit do batch + sleep para o Aiven respirar
            if len(batch_atual) >= VENDA_BATCH:
                db.session.commit()
                print(f"   ✅ Batch commitado: {vendas_criadas}/{num_vendas_alvo} vendas — aguardando {VENDA_SLEEP}s...")
                time.sleep(VENDA_SLEEP)
                vendas_geradas.extend(batch_atual)
                batch_atual = []

        # Commit do último batch (< 100)
        if batch_atual:
            db.session.commit()
            vendas_geradas.extend(batch_atual)
            print(f"   ✅ Último batch commitado: {vendas_criadas} vendas no total.")

        # -------------------------------------------------------
        # 10. DESPESAS E CONTAS A PAGAR
        # -------------------------------------------------------
        print("📉 Criando despesas e contas a pagar...")
        CATS_DESP = ["Aluguel", "Energia Elétrica", "Água", "Telefone/Internet",
                     "Salários", "Pró-labore", "Manutenção", "Marketing", "Impostos"]
        for est in estabelecimentos:
            for meses_atras in range(7):
                data_desp = date(TODAY.year, TODAY.month, 1) - timedelta(days=30 * meses_atras)
                for cat_d in random.sample(CATS_DESP, 4):
                    valor_d = fmt(random.uniform(600, 6000))
                    db.session.add(Despesa(
                        estabelecimento_id=est.id,
                        descricao=f"{cat_d} — {data_desp.strftime('%m/%Y')}",
                        categoria=cat_d,
                        tipo="fixa" if cat_d in ("Aluguel", "Salários") else "variavel",
                        valor=valor_d,
                        data_despesa=data_desp,
                        data_vencimento=data_desp + timedelta(days=5),
                        forma_pagamento="Boleto",
                        recorrente=True,
                    ))

            # Contas a pagar vinculadas aos pedidos
            for pc in PedidoCompra.query.filter_by(estabelecimento_id=est.id).all():
                if random.random() < 0.8:
                    data_venc_cp = (pc.data_pedido + timedelta(days=28)).date()
                    pago_cp = random.choice([True, False])
                    fns_est = [f for f in fornecedores if f.estabelecimento_id == est.id]
                    db.session.add(ContaPagar(
                        estabelecimento_id=est.id,
                        fornecedor_id=pc.fornecedor_id,
                        pedido_compra_id=pc.id,
                        numero_documento=pc.numero_pedido,
                        valor_original=pc.total,
                        valor_pago=pc.total if pago_cp else fmt(0),
                        valor_atual=fmt(0) if pago_cp else pc.total,
                        data_emissao=pc.data_pedido.date(),
                        data_vencimento=data_venc_cp,
                        data_pagamento=data_venc_cp if pago_cp else None,
                        status="pago" if pago_cp else "aberto",
                    ))

        db.session.commit()
        print("   ✅ Despesas e contas a pagar commitadas.")

        # -------------------------------------------------------
        # 11. CAIXA + MOVIMENTAÇÕES
        # -------------------------------------------------------
        print("💵 Gerando movimentações de caixa...")
        for est in estabelecimentos:
            funcs_est = [f for f in funcionarios if f.estabelecimento_id == est.id]
            caixa_obj = Caixa(
                estabelecimento_id=est.id,
                funcionario_id=random.choice(funcs_est).id,
                numero_caixa="001",
                saldo_inicial=fmt(random.uniform(500, 2000)),
                saldo_atual=fmt(0),
                data_abertura=datetime.combine(START_DATE, dtime(8, 0)),
                status="fechado",
            )
            db.session.add(caixa_obj)
            db.session.flush()

            for venda in [v for v in vendas_geradas
                          if v.estabelecimento_id == est.id and v.forma_pagamento != "Fiado"]:
                db.session.add(MovimentacaoCaixa(
                    caixa_id=caixa_obj.id,
                    estabelecimento_id=est.id,
                    tipo="entrada",
                    valor=venda.total,
                    forma_pagamento=venda.forma_pagamento,
                    venda_id=venda.id,
                    descricao=f"Venda {venda.codigo}",
                ))

            for desp in Despesa.query.filter_by(estabelecimento_id=est.id).all():
                if random.random() < 0.8:
                    db.session.add(MovimentacaoCaixa(
                        caixa_id=caixa_obj.id,
                        estabelecimento_id=est.id,
                        tipo="saida",
                        valor=desp.valor,
                        forma_pagamento="Boleto",
                        descricao=f"Despesa: {desp.descricao}",
                    ))

        db.session.commit()
        print("   ✅ Caixa commitado.")

        # -------------------------------------------------------
        # 12. PONTO E BANCO DE HORAS
        # -------------------------------------------------------
        print("⏰ Gerando registros de ponto e banco de horas...")
        for est in estabelecimentos:
            db.session.add(ConfiguracaoHorario(
                estabelecimento_id=est.id,
                hora_entrada=dtime(8, 0),
                hora_saida_almoco=dtime(12, 0),
                hora_retorno_almoco=dtime(13, 0),
                hora_saida=dtime(18, 0),
                tolerancia_entrada=10,
            ))

            ativos_est = [f for f in funcionarios if f.estabelecimento_id == est.id and f.ativo]
            for dia_n in range((TODAY - PONTO_START).days):
                data_p = PONTO_START + timedelta(days=dia_n)
                if data_p.weekday() >= 5:
                    continue
                for func in ativos_est:
                    atraso = random.randint(0, 20) if random.random() < 0.3 else 0
                    for tipo_r, hora_r in [
                        ("entrada",        dtime(8, atraso)),
                        ("saida_almoco",   dtime(12, random.randint(0, 10))),
                        ("retorno_almoco", dtime(13, random.randint(0, 10))),
                        ("saida",          dtime(18, random.randint(0, 15))),
                    ]:
                        db.session.add(RegistroPonto(
                            funcionario_id=func.id,
                            estabelecimento_id=est.id,
                            data=data_p,
                            hora=hora_r,
                            tipo_registro=tipo_r,
                            status="atrasado" if tipo_r == "entrada" and atraso > 10 else "normal",
                            minutos_atraso=atraso if tipo_r == "entrada" else 0,
                        ))

            # Banco de horas — UniqueConstraint (funcionario_id, mes_referencia)
            meses_bh = set()
            for mes_n in range(1, 4):
                ref = (TODAY.replace(day=1) - timedelta(days=30 * mes_n)).strftime("%Y-%m")
                meses_bh.add(ref)

            for func in ativos_est:
                for mes_ref in meses_bh:
                    db.session.add(BancoHoras(
                        funcionario_id=func.id,
                        mes_referencia=mes_ref,
                        saldo_minutos=random.randint(-120, 300),
                        horas_trabalhadas_minutos=random.randint(8000, 10000),
                        horas_esperadas_minutos=9600,
                    ))

        db.session.commit()
        print("   ✅ Ponto e banco de horas commitados.")

        # -------------------------------------------------------
        # 13. HISTÓRICO DE PREÇOS
        # -------------------------------------------------------
        print("📈 Gerando histórico de preços...")
        for est in estabelecimentos:
            funcs_est = [f for f in funcionarios if f.estabelecimento_id == est.id]
            amostra = random.sample(produtos_por_est[est.id], min(15, len(produtos_por_est[est.id])))
            for produto in amostra:
                c_ant = produto.preco_custo
                v_ant = produto.preco_venda
                c_novo = fmt(float(c_ant) * random.uniform(1.05, 1.20))
                v_novo = fmt(float(v_ant) * random.uniform(1.08, 1.25))
                margem_ant = float((v_ant - c_ant) / c_ant * 100) if float(c_ant) > 0 else 0
                margem_nov = float((v_novo - c_novo) / c_novo * 100) if float(c_novo) > 0 else 0
                produto.preco_custo = c_novo
                produto.preco_venda = v_novo
                db.session.add(HistoricoPrecos(
                    estabelecimento_id=est.id,
                    produto_id=produto.id,
                    funcionario_id=random.choice(funcs_est).id,
                    preco_custo_anterior=c_ant,
                    preco_venda_anterior=v_ant,
                    margem_anterior=fmt(margem_ant),
                    preco_custo_novo=c_novo,
                    preco_venda_novo=v_novo,
                    margem_nova=fmt(margem_nov),
                    motivo="Reajuste de custo",
                    observacoes="Aumento do fornecedor repassado ao consumidor",
                ))

        db.session.commit()
        print("   ✅ Histórico de preços commitado.")

        # -------------------------------------------------------
        # 14. MÉTRICAS DE DASHBOARD (últimos 30 dias)
        # -------------------------------------------------------
        print("📊 Gerando métricas de dashboard...")
        for est in estabelecimentos:
            for dias_n in range(30):
                data_ref = TODAY - timedelta(days=dias_n)
                vendas_dia = [v for v in vendas_geradas
                              if v.estabelecimento_id == est.id
                              and isinstance(v.data_venda, datetime)
                              and v.data_venda.date() == data_ref]
                total_d = sum(float(v.total) for v in vendas_dia)
                qtd_d   = len(vendas_dia)
                db.session.add(DashboardMetrica(
                    estabelecimento_id=est.id,
                    data_referencia=data_ref,
                    total_vendas_dia=fmt(total_d),
                    quantidade_vendas_dia=qtd_d,
                    ticket_medio_dia=fmt(total_d / qtd_d) if qtd_d else fmt(0),
                    clientes_atendidos_dia=random.randint(10, 60),
                ))

        db.session.commit()
        print("   ✅ Métricas commitadas.")

        # -------------------------------------------------------
        # 15. RELATÓRIOS AGENDADOS + LOGIN HISTORY
        # -------------------------------------------------------
        print("📅 Criando relatórios e histórico de login...")
        TIPOS_REL = ["vendas", "estoque", "financeiro", "rh"]
        for est in estabelecimentos:
            for _ in range(3):
                tipo_r = random.choice(TIPOS_REL)
                db.session.add(RelatorioAgendado(
                    estabelecimento_id=est.id,
                    nome=f"Relatório de {tipo_r.capitalize()}",
                    tipo=tipo_r,
                    formato=random.choice(["pdf", "excel"]),
                    frequencia=random.choice(["diario", "semanal", "mensal"]),
                    horario_envio=random_time(6, 10),
                    destinatarios_email_json=json.dumps([fake.email() for _ in range(random.randint(1, 3))]),
                    ativo=True,
                ))

        for func in funcionarios:
            for _ in range(random.randint(2, 6)):
                db.session.add(LoginHistory(
                    funcionario_id=func.id,
                    username=func.username,
                    estabelecimento_id=func.estabelecimento_id,
                    ip_address=fake.ipv4(),
                    dispositivo=fake.user_agent(),
                    success=random.random() < 0.9,
                    data_cadastro=NOW - timedelta(days=random.randint(1, 60)),
                ))

        db.session.commit()
        print("   ✅ Relatórios e logins commitados.")

        # -------------------------------------------------------
        # RESUMO FINAL
        # -------------------------------------------------------
        print("\n" + "=" * 60)
        print("🎉 Seed concluída com SUCESSO!")
        print("=" * 60)
        print(f"  Estabelecimentos : {len(estabelecimentos)}")
        print(f"  Funcionários     : {len(funcionarios)}")
        print(f"  Fornecedores     : {len(fornecedores)}")
        print(f"  Categorias       : {len(CATEGORIAS)} por est")
        print(f"  Produtos         : {sum(len(v) for v in produtos_por_est.values())}")
        print(f"  Clientes         : {len(clientes)}")
        print(f"  Pedidos Compra   : {len(pedidos_compra)}")
        print(f"  Vendas           : {vendas_criadas}")
        print("=" * 60)


if __name__ == "__main__":
    app = create_app()
    seed(app)