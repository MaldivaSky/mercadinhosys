#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_aiven.py — Seed STANDALONE para o banco Aiven (PostgreSQL Cloud)
======================================================================
Execute:
    python seed_aiven.py

Saída detalhada em tempo real. Sem Flask. Sem Schema Sync. Muito mais rápido.
"""

import sys
import os
import random
import json
import time
from datetime import datetime, date, timedelta, time as dtime
from decimal import Decimal, ROUND_HALF_UP

# ─────────────────────────── ENCODING (Windows) ──────────────────────────────
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ──────────────────────────── AIVEN URL ──────────────────────────────────────
AIVEN_URL = os.environ.get("DATABASE_URL_TARGET")
if not AIVEN_URL:
    print("❌ ERRO: Defina DATABASE_URL_TARGET no ambiente antes de rodar o seed.", flush=True)
    print("   Ex: $env:DATABASE_URL_TARGET='postgresql://user:pass@host:port/db?sslmode=require'", flush=True)
    import sys; sys.exit(1)

if AIVEN_URL.startswith("postgres://"):
    AIVEN_URL = AIVEN_URL.replace("postgres://", "postgresql://", 1)

# ──────────────────────── SQLALCHEMY STANDALONE ──────────────────────────────
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# ─── Importamos os models diretamente (sem create_app) ───────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Precisamos de um app mínimo só para carregar os models com MetaData
from flask import Flask as _Flask
_app = _Flask(__name__)
_app.config["SQLALCHEMY_DATABASE_URI"] = AIVEN_URL
_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

from app.models import (
    db as _db,
    Estabelecimento, Configuracao, Funcionario, Beneficio,
    FuncionarioBeneficio, BancoHoras, RegistroPonto, ConfiguracaoHorario,
    Fornecedor, CategoriaProduto, Produto, ProdutoLote,
    Cliente, PedidoCompra, PedidoCompraItem, Venda, VendaItem,
    MovimentacaoEstoque, HistoricoPrecos, ContaPagar, ContaReceber,
    Despesa, Caixa, MovimentacaoCaixa, LoginHistory,
    RelatorioAgendado, DashboardMetrica,
)
_db.init_app(_app)

# ──────────────────────── HELPERS ────────────────────────────────────────────
from faker import Faker
fake = Faker("pt_BR")

def ok(msg):   print(f"   ✅ {msg}", flush=True)
def info(msg): print(f"   → {msg}", flush=True)
def title(msg):
    print(flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  {msg}", flush=True)
    print(f"{'='*60}", flush=True)

def fmt(v):
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def rdate(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))

def rdatetime(start: date, end: date) -> datetime:
    d = rdate(start, end)
    return datetime(d.year, d.month, d.day, random.randint(8, 21),
                    random.choice([0, 10, 20, 30, 40, 50]))

TODAY       = date.today()
START_DATE  = TODAY - timedelta(days=180)
PONTO_START = TODAY - timedelta(days=30)

# ─────────────────────────── DADOS REAIS ─────────────────────────────────────
CATEGORIAS = ["Bebidas", "Laticínios", "Mercearia", "Limpeza", "Higiene Pessoal",
               "Hortifrúti", "Carnes", "Padaria", "Congelados", "Pet Shop"]

PRODUTOS_REAIS = [
    ("Arroz Branco Tipo 1 5kg", "Camil", "Mercearia", 20.00, 29.90),
    ("Arroz Integral 5kg", "Tio João", "Mercearia", 18.00, 26.90),
    ("Feijão Carioca 1kg", "Camil", "Mercearia", 7.50, 11.90),
    ("Feijão Preto 1kg", "Kicaldo", "Mercearia", 8.00, 12.90),
    ("Óleo de Soja 900ml", "Soya", "Mercearia", 5.00, 7.99),
    ("Açúcar Refinado 1kg", "União", "Mercearia", 3.50, 5.49),
    ("Café Torrado Moído 500g", "Pilão", "Mercearia", 12.00, 18.90),
    ("Café em Pó 500g", "Três Corações", "Mercearia", 11.50, 17.90),
    ("Farinha de Trigo 1kg", "Dona Benta", "Mercearia", 3.20, 5.49),
    ("Macarrão Espaguete 500g", "Adria", "Mercearia", 2.80, 4.49),
    ("Molho de Tomate 340g", "Pomarola", "Mercearia", 2.50, 4.29),
    ("Sardinha em Lata 125g", "Gomes da Costa", "Mercearia", 4.50, 7.99),
    ("Atum Ralado 170g", "Gomes da Costa", "Mercearia", 5.00, 8.90),
    ("Leite UHT Integral 1L", "Italac", "Laticínios", 3.50, 5.49),
    ("Leite UHT Desnatado 1L", "Italac", "Laticínios", 3.50, 5.49),
    ("Leite em Pó Integral 400g", "Ninho", "Laticínios", 15.00, 24.90),
    ("Iogurte Natural 170g", "Nestlé", "Laticínios", 2.50, 4.49),
    ("Queijo Muçarela Fatiado 150g", "Président", "Laticínios", 12.00, 19.90),
    ("Requeijão Cremoso 250g", "Vigor", "Laticínios", 5.00, 8.49),
    ("Manteiga com Sal 200g", "Aviação", "Laticínios", 7.00, 11.90),
    ("Creme de Leite 200g", "Nestlé", "Laticínios", 3.00, 5.29),
    ("Leite Condensado 395g", "Moça", "Laticínios", 4.50, 7.49),
    ("Coca-Cola 2L", "Coca-Cola", "Bebidas", 6.00, 9.99),
    ("Guaraná Antarctica 2L", "Antarctica", "Bebidas", 5.00, 8.49),
    ("Suco de Laranja Del Valle 1L", "Del Valle", "Bebidas", 4.00, 6.99),
    ("Água Mineral Crystal 500ml", "Crystal", "Bebidas", 1.20, 2.49),
    ("Água Mineral Crystal 1.5L", "Crystal", "Bebidas", 2.00, 3.99),
    ("Cerveja Skol 350ml Lata", "Skol", "Bebidas", 2.50, 4.29),
    ("Cerveja Brahma 350ml Lata", "Brahma", "Bebidas", 2.50, 4.29),
    ("Vinho Tinto Gato Negro 750ml", "Gato Negro", "Bebidas", 25.00, 39.90),
    ("Sabão em Pó Omo 1kg", "Omo", "Limpeza", 12.00, 19.90),
    ("Amaciante Downy 1L", "Downy", "Limpeza", 10.00, 16.90),
    ("Detergente Ypê 500ml", "Ypê", "Limpeza", 1.80, 2.99),
    ("Água Sanitária Q-Boa 1L", "Q-Boa", "Limpeza", 3.00, 5.49),
    ("Desinfetante Pinho Sol 500ml", "Pinho Sol", "Limpeza", 4.00, 6.99),
    ("Palha de Aço Bombril c/8", "Bombril", "Limpeza", 1.00, 1.99),
    ("Limpador Veja Multiuso 500ml", "Veja", "Limpeza", 4.00, 6.99),
    ("Papel Higiênico Neve 12 rolos", "Neve", "Higiene Pessoal", 12.00, 19.90),
    ("Shampoo Seda 325ml", "Seda", "Higiene Pessoal", 8.00, 13.90),
    ("Sabonete Dove 90g", "Dove", "Higiene Pessoal", 2.00, 3.49),
    ("Creme Dental Colgate 90g", "Colgate", "Higiene Pessoal", 3.00, 5.49),
    ("Desodorante Rexona Aerosol 150ml", "Rexona", "Higiene Pessoal", 10.00, 16.90),
    ("Fralda Pampers P c/22", "Pampers", "Higiene Pessoal", 35.00, 54.90),
    ("Fralda Pampers M c/20", "Pampers", "Higiene Pessoal", 36.00, 55.90),
    ("Absorvente Always Noturno c/8", "Always", "Higiene Pessoal", 8.00, 13.90),
    ("Batata Inglesa 1kg", "In natura", "Hortifrúti", 3.00, 5.99),
    ("Cebola 1kg", "In natura", "Hortifrúti", 4.00, 7.49),
    ("Tomate 1kg", "In natura", "Hortifrúti", 5.00, 8.99),
    ("Banana Prata 1kg", "In natura", "Hortifrúti", 4.00, 6.99),
    ("Maçã Fuji 1kg", "In natura", "Hortifrúti", 6.00, 9.99),
    ("Laranja Pera 1kg", "In natura", "Hortifrúti", 3.00, 5.49),
    ("Peito de Frango Sadia 1kg", "Sadia", "Carnes", 14.00, 22.90),
    ("Carne Moída Friboi 500g", "Friboi", "Carnes", 12.00, 19.90),
    ("Alcatra Friboi 1kg", "Friboi", "Carnes", 35.00, 54.90),
    ("Linguiça Toscana Aurora 500g", "Aurora", "Carnes", 15.00, 24.90),
    ("Hambúrguer Sadia 672g", "Sadia", "Carnes", 12.00, 19.90),
    ("Pizza Margherita Forno de Minas 460g", "Forno de Minas", "Congelados", 15.00, 24.90),
    ("Sorvete Kibon 1.5L", "Kibon", "Congelados", 18.00, 29.90),
    ("Lasanha Sadia 600g", "Sadia", "Congelados", 14.00, 22.90),
    ("Pão de Forma Pullman 500g", "Pullman", "Padaria", 5.00, 8.49),
    ("Biscoito Cream Cracker Tostines 200g", "Tostines", "Padaria", 3.00, 5.29),
    ("Biscoito Recheado Trakinas 126g", "Trakinas", "Padaria", 2.50, 4.49),
    ("Bolo de Chocolate Ana Maria 270g", "Ana Maria", "Padaria", 4.00, 6.99),
    ("Ração Pedigree Cães Adultos 10kg", "Pedigree", "Pet Shop", 60.00, 99.90),
    ("Ração Whiskas Gatos 5kg", "Whiskas", "Pet Shop", 40.00, 69.90),
]

FORNECEDORES = [
    "Camil Alimentos", "JBS / Friboi", "Sadia / BRF", "Nestlé Brasil",
    "Coca-Cola FEMSA", "Ambev", "Unilever Brasil", "P&G Brasil",
    "Kimberly-Clark", "Ypê Indústrias", "Bombril", "Johnson & Johnson",
    "Colgate-Palmolive", "Seara Alimentos", "Aurora Alimentos",
    "Italac Alimentos", "Vigor Alimentos", "Président Lactalis",
    "Pedigree / Mars", "Whiskas / Mars",
]

CLIENTES = [
    "João da Silva", "Maria Santos", "José Oliveira", "Ana Souza", "Carlos Lima",
    "Fernanda Rocha", "Antônio Alves", "Mariana Costa", "Paulo Pereira",
    "Patrícia Ferreira", "Ricardo Martins", "Camila Rodrigues", "Lucas Nunes",
    "Juliana Mendes", "Pedro Carvalho", "Amanda Ribeiro", "Bruno Teixeira",
    "Larissa Gomes", "Daniel Barbosa", "Natália Dias", "Rafael Cardoso",
    "Bianca Monteiro", "Marcelo Barros", "Luciana Freitas", "Felipe Azevedo",
    "Vanessa Correia", "Gustavo Cunha", "Tatiana Fogaça", "Leonardo Viana",
    "Sabrina Duarte",
]

FUNC_TEMPLATES = [
    ("Rafael Maldivas",  "admin",    "ADMIN",      "Proprietário",            5000.00),
    ("Ana Paula Caixa",  "caixa",    "CAIXA",      "Operador de Caixa",       1850.00),
    ("Pedro Estoque",    "estoque",  "FUNCIONARIO","Auxiliar de Estoque",      1700.00),
    ("Mariana Auxiliar", "auxiliar", "FUNCIONARIO","Auxiliar Administrativo",  1900.00),
    ("João Repositor",   "repositor","FUNCIONARIO","Repositor",                1600.00),
]
SENHAS = {"ADMIN": "admin123", "CAIXA": "caixa123", "FUNCIONARIO": "func123"}


# ─────────────────────────────── SEED ────────────────────────────────────────
def run():
    title("SEED AIVEN — MercadinhoSys")
    print(f"  Banco: {AIVEN_URL[:70]}...", flush=True)
    print(f"  Início: {datetime.now().strftime('%H:%M:%S')}", flush=True)

    with _app.app_context():

        # ── APAGAR E RECRIAR ────────────────────────────────────────────────
        print("\n🗑️  Apagando todas as tabelas...", flush=True)
        _db.drop_all()
        ok("Tabelas apagadas")

        print("🏗️  Criando schema completo...", flush=True)
        _db.create_all()
        ok("Schema criado")

        seq = {}
        def nxt(eid, k):
            seq[eid][k] += 1
            return seq[eid][k]

        # ── 1. ESTABELECIMENTOS ─────────────────────────────────────────────
        print("\n🏪 [1/13] Estabelecimentos...", flush=True)
        est1 = Estabelecimento(
            nome_fantasia="Mercadinho Maldivas", razao_social="Maldivas Shopp Ltda",
            cnpj="12.345.678/0001-99", inscricao_estadual="123456789",
            telefone="(21) 98888-0001", email="rafaelmaldivas@gmail.com",
            cep="20041-008", logradouro="Rua da Carioca", numero="100",
            bairro="Centro", cidade="Rio de Janeiro", estado="RJ", pais="Brasil",
            ativo=True, regime_tributario="SIMPLES NACIONAL",
            data_abertura=date(2020, 1, 1), plano="Premium", plano_status="ativo",
        )
        est2 = Estabelecimento(
            nome_fantasia="Supermercado Praia", razao_social="Praia Comércio de Alimentos Ltda",
            cnpj="98.765.432/0001-11", inscricao_estadual="987654321",
            telefone="(21) 98888-0002", email="contato@superpraia.com.br",
            cep="22010-010", logradouro="Av. Atlântica", numero="2000",
            bairro="Copacabana", cidade="Rio de Janeiro", estado="RJ", pais="Brasil",
            ativo=True, regime_tributario="LUCRO PRESUMIDO",
            data_abertura=date(2019, 5, 10), plano="Advanced", plano_status="ativo",
        )
        _db.session.add_all([est1, est2])
        _db.session.flush()
        estabelecimentos = [est1, est2]
        for est in estabelecimentos:
            seq[est.id] = {"lote": 0, "pedido": 0, "venda": 0, "prod": 0}
            _db.session.add(Configuracao(
                estabelecimento_id=est.id,
                formas_pagamento=json.dumps(["Dinheiro","Pix","Cartão de Crédito","Cartão de Débito","Fiado"]),
                controlar_validade=True, alerta_estoque_minimo=True, permitir_venda_sem_estoque=False,
            ))
        _db.session.flush()
        ok(f"2 estabelecimentos criados (IDs: {est1.id}, {est2.id})")

        # ── 2. FUNCIONÁRIOS ─────────────────────────────────────────────────
        print("\n👥 [2/13] Funcionários...", flush=True)
        funcionarios = []
        for idx, est in enumerate(estabelecimentos):
            for t_nome, t_user, t_role, t_cargo, t_sal in FUNC_TEMPLATES:
                username = t_user if idx == 0 else f"{t_user}2"
                f = Funcionario(
                    estabelecimento_id=est.id, nome=t_nome, username=username,
                    role=t_role, cargo=t_cargo, salario_base=t_sal,
                    cpf=fake.cpf(), rg=fake.rg(),
                    data_nascimento=fake.date_of_birth(minimum_age=22, maximum_age=55),
                    celular=fake.cellphone_number(),
                    email=f"{username}@mercadinho.com",
                    data_admissao=rdate(date(2020,1,1), TODAY - timedelta(days=60)),
                    ativo=True, cep=est.cep, logradouro=est.logradouro,
                    numero=str(random.randint(10,999)), bairro=est.bairro,
                    cidade=est.cidade, estado=est.estado,
                    permissoes_json=json.dumps({
                        "pdv": t_role in ("ADMIN","CAIXA"),
                        "estoque": t_role in ("ADMIN","FUNCIONARIO"),
                        "compras": t_role == "ADMIN",
                        "financeiro": t_role == "ADMIN",
                        "configuracoes": t_role == "ADMIN",
                    }),
                )
                f.set_senha(SENHAS[t_role])
                _db.session.add(f)
                funcionarios.append(f)
                info(f"  {username} ({t_role}) — {est.nome_fantasia}")
        _db.session.flush()
        ok(f"{len(funcionarios)} funcionários criados")

        # ── 3. BENEFÍCIOS ───────────────────────────────────────────────────
        print("\n🎁 [3/13] Benefícios...", flush=True)
        beneficios = []
        for est in estabelecimentos:
            for nome_b, val_b in [("Vale Alimentação",450),("Vale Transporte",220),("Plano de Saúde",150)]:
                b = Beneficio(estabelecimento_id=est.id, nome=nome_b, valor_padrao=val_b, ativo=True)
                _db.session.add(b)
                beneficios.append(b)
        _db.session.flush()
        for func in funcionarios:
            for b in [x for x in beneficios if x.estabelecimento_id == func.estabelecimento_id]:
                _db.session.add(FuncionarioBeneficio(funcionario_id=func.id, beneficio_id=b.id, valor=b.valor_padrao, ativo=True))
        _db.session.flush()
        ok(f"{len(beneficios)} benefícios + vínculos criados")

        # ── 4. FORNECEDORES ─────────────────────────────────────────────────
        print("\n🏭 [4/13] Fornecedores...", flush=True)
        fornecedores = []
        cnpjs_usados = set()
        for est in estabelecimentos:
            nomes = random.sample(FORNECEDORES, 10)
            for nome_f in nomes:
                cnpj = fake.cnpj()
                while cnpj in cnpjs_usados:
                    cnpj = fake.cnpj()
                cnpjs_usados.add(cnpj)
                fn = Fornecedor(
                    estabelecimento_id=est.id, nome_fantasia=nome_f,
                    razao_social=f"{nome_f} Ltda", cnpj=cnpj,
                    inscricao_estadual=fake.estado_sigla()+str(random.randint(10000000,99999999)),
                    telefone=fake.phone_number(), email=f"comercial@{nome_f.split()[0].lower()}.com.br",
                    cep=fake.postcode(), logradouro=fake.street_name(),
                    numero=str(random.randint(1,999)), bairro=fake.bairro(),
                    cidade=fake.city(), estado=fake.estado_sigla(), ativo=True,
                )
                _db.session.add(fn)
                fornecedores.append(fn)
        _db.session.flush()
        ok(f"{len(fornecedores)} fornecedores criados")

        # ── 5. CATEGORIAS ────────────────────────────────────────────────────
        print("\n🏷️  [5/13] Categorias de produto...", flush=True)
        categorias_por_est = {}
        for est in estabelecimentos:
            cat_dict = {}
            for i, nome_cat in enumerate(CATEGORIAS, 1):
                cat = CategoriaProduto(
                    estabelecimento_id=est.id, nome=nome_cat,
                    codigo=f"CAT{est.id:02d}{i:03d}", ativo=True,
                )
                _db.session.add(cat)
                _db.session.flush()
                cat_dict[nome_cat] = cat
            categorias_por_est[est.id] = cat_dict
        ok(f"{len(CATEGORIAS)*2} categorias criadas")

        # ── 6. PRODUTOS + LOTES ──────────────────────────────────────────────
        print(f"\n📦 [6/13] Produtos ({len(PRODUTOS_REAIS)} por distribuição em 2 lojas)...", flush=True)
        produtos_por_est = {est.id: [] for est in estabelecimentos}
        lotes_mem = {}

        for i, (nome_p, marca_p, cat_nome, custo_p, venda_p) in enumerate(PRODUTOS_REAIS, 1):
            est = random.choice(estabelecimentos)
            cat = categorias_por_est[est.id][cat_nome]
            fns_est = [f for f in fornecedores if f.estabelecimento_id == est.id]
            fornecedor = random.choice(fns_est)
            idx_p = nxt(est.id, "prod")
            cod = f"{cat_nome[:2].upper()}{est.id:02d}{idx_p:04d}"

            prod = Produto(
                estabelecimento_id=est.id, categoria_id=cat.id, fornecedor_id=fornecedor.id,
                nome=nome_p, codigo_interno=cod, preco_custo=fmt(custo_p),
                preco_venda=fmt(venda_p), quantidade=0,
                quantidade_minima=random.randint(5,20), unidade_medida="UN",
                ncm=fake.numerify(text="########"), marca=marca_p, fabricante=marca_p,
                tipo=cat_nome, subcategoria="Geral", ativo=True,
                imagem_url=f"https://via.placeholder.com/300x300?text={nome_p[:15].replace(' ','+')}",
                controlar_validade=True,
            )
            _db.session.add(prod)
            _db.session.flush()
            produtos_por_est[est.id].append(prod)
            lotes_mem[prod.id] = []

            for _ in range(2):
                data_ent = rdate(START_DATE - timedelta(days=60), TODAY - timedelta(days=1))
                data_val = data_ent + timedelta(days=random.randint(60, 365))
                qtd = random.randint(80, 250)
                num_lote = f"LOT{est.id:02d}{nxt(est.id,'lote'):06d}"
                lote = ProdutoLote(
                    estabelecimento_id=est.id, produto_id=prod.id,
                    fornecedor_id=fornecedor.id, numero_lote=num_lote,
                    quantidade=qtd, quantidade_inicial=qtd, data_entrada=data_ent,
                    data_validade=data_val, preco_custo_unitario=prod.preco_custo, ativo=True,
                )
                _db.session.add(lote)
                prod.quantidade += qtd
                lotes_mem[prod.id].append({"obj": lote, "validade": data_val})
            lotes_mem[prod.id].sort(key=lambda x: x["validade"])

            if i % 10 == 0:
                info(f"  {i}/{len(PRODUTOS_REAIS)} produtos processados...")
        _db.session.flush()
        total_prods = sum(len(v) for v in produtos_por_est.values())
        ok(f"{total_prods} produtos criados com lotes")

        # ── 7. CLIENTES ──────────────────────────────────────────────────────
        print("\n👤 [7/13] Clientes...", flush=True)
        clientes = []
        cpfs_usados = set()
        for nome_cli in CLIENTES:
            est = random.choice(estabelecimentos)
            cpf = fake.cpf()
            for _ in range(30):
                if cpf not in cpfs_usados:
                    break
                cpf = fake.cpf()
            cpfs_usados.add(cpf)
            cli = Cliente(
                estabelecimento_id=est.id, nome=nome_cli, cpf=cpf, rg=fake.rg(),
                data_nascimento=fake.date_of_birth(minimum_age=18, maximum_age=80),
                telefone=fake.phone_number(), celular=fake.cellphone_number(),
                email=fake.email(), cep=fake.postcode(), logradouro=fake.street_name(),
                numero=str(random.randint(1,999)), bairro=fake.bairro(),
                cidade=fake.city(), estado=fake.estado_sigla(),
                ativo=True, limite_credito=fmt(random.uniform(200, 2000)),
            )
            _db.session.add(cli)
            clientes.append(cli)
        _db.session.flush()
        ok(f"{len(clientes)} clientes criados")

        # ── 8. PEDIDOS DE COMPRA ─────────────────────────────────────────────
        print("\n📋 [8/13] Pedidos de compra...", flush=True)
        pedidos_compra = []
        for est in estabelecimentos:
            funcs_est = [f for f in funcionarios if f.estabelecimento_id == est.id]
            fns_est   = [f for f in fornecedores if f.estabelecimento_id == est.id]
            for produto in produtos_por_est[est.id]:
                data_ped = rdate(START_DATE - timedelta(days=30), TODAY - timedelta(days=1))
                num_pc = f"PC{est.id:02d}-{nxt(est.id,'pedido'):05d}"
                pc = PedidoCompra(
                    estabelecimento_id=est.id, fornecedor_id=random.choice(fns_est).id,
                    funcionario_id=random.choice(funcs_est).id, numero_pedido=num_pc,
                    data_pedido=datetime.combine(data_ped, dtime(10,0)),
                    data_recebimento=data_ped + timedelta(days=random.randint(1,7)),
                    status="recebido", subtotal=0, desconto=0, frete=0, total=0,
                )
                _db.session.add(pc)
                _db.session.flush()
                pedidos_compra.append(pc)

                qtd_sol = random.randint(50, 200)
                t_it = float(produto.preco_custo) * qtd_sol
                _db.session.add(PedidoCompraItem(
                    pedido_id=pc.id, produto_id=produto.id,
                    produto_nome=produto.nome, produto_unidade="UN",
                    quantidade_solicitada=qtd_sol, quantidade_recebida=qtd_sol,
                    preco_unitario=produto.preco_custo, total_item=t_it, status="recebido",
                ))
                if lotes_mem.get(produto.id):
                    lotes_mem[produto.id][0]["obj"].quantidade += qtd_sol
                produto.quantidade += qtd_sol
                pc.subtotal = t_it; pc.total = t_it
                _db.session.add(MovimentacaoEstoque(
                    estabelecimento_id=est.id, produto_id=produto.id,
                    pedido_compra_id=pc.id, funcionario_id=pc.funcionario_id,
                    tipo="entrada", quantidade=qtd_sol,
                    quantidade_anterior=produto.quantidade - qtd_sol,
                    quantidade_atual=produto.quantidade, custo_unitario=produto.preco_custo,
                    valor_total=t_it, motivo="Compra",
                ))
        _db.session.commit()
        ok(f"{len(pedidos_compra)} pedidos de compra + itens commitados")

        # ── 9. VENDAS ─────────────────────────────────────────────────────────
        print("\n💰 [9/13] Vendas (1800 em batches de 100 — 1 flush por batch)...", flush=True)

        funcs_por_est = {est.id: [f for f in funcionarios if f.estabelecimento_id == est.id] for est in estabelecimentos}
        clis_por_est  = {}
        for cli in clientes:
            clis_por_est.setdefault(cli.estabelecimento_id, []).append(cli)

        FORMAS = ["Dinheiro","Pix","Cartão de Crédito","Cartão de Débito","Fiado"]
        PESOS  = [40, 30, 15, 10, 5]

        def consumir(pid, qtd_desejada):
            restante = qtd_desejada
            for l in lotes_mem.get(pid, []):
                if restante <= 0: break
                usar = min(restante, l["obj"].quantidade)
                if usar > 0:
                    l["obj"].quantidade -= usar
                    restante -= usar
            return qtd_desejada - restante

        vendas_todas = []
        vendas_criadas = 0
        tentativas     = 0
        inicio_vendas  = time.time()

        # Acumula (venda_obj, [(prod, qtd, preco, t_it)], forma, cli) por batch
        batch_vendas = []   # Venda ORM objects (sem ID ainda)
        batch_itens  = []   # lista de listas de (prod, qtd, preco, t_it)
        batch_meta   = []   # (forma_pag, cli, cod_v, data_v, est, func) para ContaReceber

        def commit_batch():
            """Flush em batch: 1 round-trip para N vendas, depois add itens e commit."""
            if not batch_vendas:
                return

            # 1 flush para obter IDs de todas as vendas do batch de uma vez
            _db.session.flush()

            for venda, itens_v, (forma, cli, cod_v, data_v, est_v, func_v) in zip(batch_vendas, batch_itens, batch_meta):
                for prod, qtd, preco, t_it in itens_v:
                    _db.session.add(VendaItem(
                        venda_id=venda.id, produto_id=prod.id, produto_nome=prod.nome,
                        produto_codigo=prod.codigo_interno, produto_unidade="UN",
                        quantidade=qtd, preco_unitario=fmt(preco), desconto=0,
                        total_item=fmt(t_it), custo_unitario=prod.preco_custo,
                        margem_lucro_real=fmt((preco - float(prod.preco_custo)) * qtd),
                    ))
                    _db.session.add(MovimentacaoEstoque(
                        estabelecimento_id=est_v.id, produto_id=prod.id, venda_id=venda.id,
                        funcionario_id=func_v.id, tipo="saida", quantidade=qtd,
                        quantidade_anterior=prod.quantidade + qtd, quantidade_atual=prod.quantidade,
                        custo_unitario=prod.preco_custo, valor_total=fmt(t_it), motivo="Venda",
                    ))
                if forma == "Fiado" and cli:
                    pago = random.random() < 0.6
                    _db.session.add(ContaReceber(
                        estabelecimento_id=est_v.id, cliente_id=cli.id, venda_id=venda.id,
                        numero_documento=f"CR-{cod_v}",
                        valor_original=fmt(float(venda.total)),
                        valor_recebido=fmt(float(venda.total)) if pago else fmt(0),
                        valor_atual=fmt(0) if pago else fmt(float(venda.total)),
                        data_emissao=data_v.date(),
                        data_vencimento=(data_v + timedelta(days=30)).date(),
                        data_recebimento=(data_v + timedelta(days=30)).date() if pago else None,
                        status="pago" if pago else "aberto",
                    ))

            _db.session.commit()
            elapsed = time.time() - inicio_vendas
            n = len(vendas_todas)
            eta   = elapsed / n * (1800 - n) if n < 1800 else 0
            print(f"   💳 Batch commitado: {n:4d}/1800 vendas  "
                  f"({elapsed:.1f}s decorridos, ETA ~{eta:.0f}s)", flush=True)

            batch_vendas.clear()
            batch_itens.clear()
            batch_meta.clear()

        while vendas_criadas < 1800 and tentativas < 5400:
            tentativas += 1
            est  = random.choice(estabelecimentos)
            data_v = rdatetime(START_DATE, TODAY - timedelta(days=1))
            func = random.choice(funcs_por_est[est.id])
            clis = clis_por_est.get(est.id, [])
            cli  = random.choice(clis) if clis and random.random() < 0.7 else None
            forma = random.choices(FORMAS, weights=PESOS)[0]

            prod_ok = [p for p in produtos_por_est[est.id] if p.quantidade > 0]
            if not prod_ok: continue

            num_it = random.randint(1, min(6, len(prod_ok)))
            prods_sel = random.sample(prod_ok, num_it)
            itens  = []
            total  = 0.0

            for prod in prods_sel:
                qtd_c = consumir(prod.id, random.randint(1, 4))
                if qtd_c == 0: continue
                preco = float(prod.preco_venda)
                t_it  = preco * qtd_c
                itens.append((prod, qtd_c, preco, t_it))
                total += t_it
                prod.quantidade -= qtd_c

            if not itens: continue

            cod_v = f"V{est.id:02d}-{nxt(est.id,'venda'):07d}"
            venda = Venda(
                estabelecimento_id=est.id, cliente_id=cli.id if cli else None,
                funcionario_id=func.id, codigo=cod_v, data_venda=data_v,
                status="finalizada", forma_pagamento=forma,
                subtotal=fmt(total), desconto=0, total=fmt(total),
                valor_recebido=fmt(total), troco=0, quantidade_itens=len(itens),
            )
            _db.session.add(venda)
            batch_vendas.append(venda)
            batch_itens.append(itens)
            batch_meta.append((forma, cli, cod_v, data_v, est, func))
            vendas_todas.append(venda)
            vendas_criadas += 1

            if len(batch_vendas) >= 100:
                commit_batch()

        # Último batch parcial
        if batch_vendas:
            commit_batch()

        ok(f"{vendas_criadas} vendas commitadas")


        # ── 10. DESPESAS + CONTAS A PAGAR ────────────────────────────────────
        print("\n📉 [10/13] Despesas e contas a pagar...", flush=True)
        CATS_DESP = {
            "Aluguel":             (2000, 4000),
            "Energia Elétrica":    (400,  800),
            "Água":                (150,  300),
            "Telefone/Internet":   (150,  350),
            "Salários":            (3000, 6000),
        }
        for est in estabelecimentos:
            for m in range(7):
                data_d = date(TODAY.year, TODAY.month, 1) - timedelta(days=30*m)
                for cat_d, (vmin, vmax) in CATS_DESP.items():
                    _db.session.add(Despesa(
                        estabelecimento_id=est.id, descricao=f"{cat_d} — {data_d.strftime('%m/%Y')}",
                        categoria=cat_d, tipo="fixa", valor=fmt(random.uniform(vmin, vmax)),
                        data_despesa=data_d, data_vencimento=data_d+timedelta(days=5),
                        forma_pagamento="Boleto", recorrente=True,
                    ))

            for pc in PedidoCompra.query.filter_by(estabelecimento_id=est.id).all():
                if random.random() < 0.8:
                    pago_cp = random.choice([True, False])
                    _db.session.add(ContaPagar(
                        estabelecimento_id=est.id, fornecedor_id=pc.fornecedor_id,
                        pedido_compra_id=pc.id, numero_documento=pc.numero_pedido,
                        valor_original=pc.total,
                        valor_pago=pc.total if pago_cp else fmt(0),
                        valor_atual=fmt(0) if pago_cp else pc.total,
                        data_emissao=pc.data_pedido.date(),
                        data_vencimento=(pc.data_pedido + timedelta(days=28)).date(),
                        data_pagamento=(pc.data_pedido + timedelta(days=28)).date() if pago_cp else None,
                        status="pago" if pago_cp else "aberto",
                    ))
        _db.session.commit()
        ok("Despesas e contas a pagar commitadas")

        # ── 11. CAIXA ────────────────────────────────────────────────────────
        print("\n💵 [11/13] Caixa e movimentações...", flush=True)
        for est in estabelecimentos:
            funcs_est = [f for f in funcionarios if f.estabelecimento_id == est.id]
            caixa = Caixa(
                estabelecimento_id=est.id, funcionario_id=random.choice(funcs_est).id,
                numero_caixa="001", saldo_inicial=fmt(random.uniform(500,2000)),
                saldo_atual=fmt(0),
                data_abertura=datetime.combine(START_DATE, dtime(8,0)), status="fechado",
            )
            _db.session.add(caixa)
            _db.session.flush()
            count_mov = 0
            for v in [x for x in vendas_todas if x.estabelecimento_id == est.id and x.forma_pagamento != "Fiado"]:
                _db.session.add(MovimentacaoCaixa(
                    caixa_id=caixa.id, estabelecimento_id=est.id, tipo="entrada",
                    valor=v.total, forma_pagamento=v.forma_pagamento,
                    venda_id=v.id, descricao=f"Venda {v.codigo}",
                ))
                count_mov += 1
            info(f"  {count_mov} movimentações de caixa — {est.nome_fantasia}")
        _db.session.commit()
        ok("Caixas commitados")

        # ── 12. PONTO + BANCO DE HORAS ───────────────────────────────────────
        print("\n⏰ [12/13] Registro de ponto (últimos 30 dias)...", flush=True)
        for est in estabelecimentos:
            _db.session.add(ConfiguracaoHorario(
                estabelecimento_id=est.id, hora_entrada=dtime(8,0),
                hora_saida_almoco=dtime(12,0), hora_retorno_almoco=dtime(13,0),
                hora_saida=dtime(18,0), tolerancia_entrada=10,
            ))
            ativos = [f for f in funcionarios if f.estabelecimento_id == est.id and f.ativo]
            dias_gerados = 0
            for dia_n in range((TODAY - PONTO_START).days):
                d = PONTO_START + timedelta(days=dia_n)
                if d.weekday() >= 5: continue
                for func in ativos:
                    atraso = random.randint(0,20) if random.random() < 0.3 else 0
                    for tipo_r, hora_r in [
                        ("entrada",        dtime(8, atraso)),
                        ("saida_almoco",   dtime(12, random.randint(0,10))),
                        ("retorno_almoco", dtime(13, random.randint(0,10))),
                        ("saida",          dtime(18, random.randint(0,15))),
                    ]:
                        _db.session.add(RegistroPonto(
                            funcionario_id=func.id, estabelecimento_id=est.id,
                            data=d, hora=hora_r, tipo_registro=tipo_r,
                            status="atrasado" if tipo_r=="entrada" and atraso>10 else "normal",
                            minutos_atraso=atraso if tipo_r=="entrada" else 0,
                        ))
                dias_gerados += 1

            meses_bh = {(TODAY.replace(day=1) - timedelta(days=30*m)).strftime("%Y-%m") for m in range(1,4)}
            for func in ativos:
                for mes_ref in meses_bh:
                    _db.session.add(BancoHoras(
                        funcionario_id=func.id, mes_referencia=mes_ref,
                        saldo_minutos=random.randint(-120,300),
                        horas_trabalhadas_minutos=random.randint(8000,10000),
                        horas_esperadas_minutos=9600,
                    ))
        _db.session.commit()
        ok("Ponto e banco de horas commitados")

        # ── 13. MÉTRICAS + HISTÓRICO DE PREÇOS + RELATÓRIOS ─────────────────
        print("\n📊 [13/13] Métricas, histórico de preços, logins...", flush=True)
        for est in estabelecimentos:
            funcs_est = [f for f in funcionarios if f.estabelecimento_id == est.id]
            # Histórico de preços
            for prod in random.sample(produtos_por_est[est.id], min(10, len(produtos_por_est[est.id]))):
                c_ant, v_ant = prod.preco_custo, prod.preco_venda
                c_novo = fmt(float(c_ant) * random.uniform(1.05, 1.20))
                v_novo = fmt(float(v_ant) * random.uniform(1.08, 1.25))
                prod.preco_custo = c_novo; prod.preco_venda = v_novo
                _db.session.add(HistoricoPrecos(
                    estabelecimento_id=est.id, produto_id=prod.id,
                    funcionario_id=random.choice(funcs_est).id,
                    preco_custo_anterior=c_ant, preco_venda_anterior=v_ant,
                    margem_anterior=fmt(float((v_ant-c_ant)/c_ant*100) if float(c_ant)>0 else 0),
                    preco_custo_novo=c_novo, preco_venda_novo=v_novo,
                    margem_nova=fmt(float((v_novo-c_novo)/c_novo*100) if float(c_novo)>0 else 0),
                    motivo="Reajuste fornecedor",
                ))
            # Métricas dos últimos 30 dias
            for d_n in range(30):
                d_ref = TODAY - timedelta(days=d_n)
                vd = [v for v in vendas_todas if v.estabelecimento_id==est.id
                      and isinstance(v.data_venda, datetime) and v.data_venda.date()==d_ref]
                t_dia = sum(float(v.total) for v in vd)
                _db.session.add(DashboardMetrica(
                    estabelecimento_id=est.id, data_referencia=d_ref,
                    total_vendas_dia=fmt(t_dia), quantidade_vendas_dia=len(vd),
                    ticket_medio_dia=fmt(t_dia/len(vd)) if vd else fmt(0),
                    clientes_atendidos_dia=random.randint(10,60),
                ))
            # Relatórios agendados
            for tipo_r in ["vendas","estoque","financeiro"]:
                _db.session.add(RelatorioAgendado(
                    estabelecimento_id=est.id, nome=f"Relatório de {tipo_r.capitalize()}",
                    tipo=tipo_r, formato="pdf", frequencia="semanal",
                    horario_envio=dtime(7,0),
                    destinatarios_email_json=json.dumps([fake.email()]), ativo=True,
                ))
            # Login history
            for func in funcs_est:
                for _ in range(random.randint(2,5)):
                    _db.session.add(LoginHistory(
                        funcionario_id=func.id, username=func.username,
                        estabelecimento_id=est.id, ip_address=fake.ipv4(),
                        dispositivo=fake.user_agent(), success=random.random()<0.9,
                        data_cadastro=datetime.utcnow() - timedelta(days=random.randint(1,60)),
                    ))
        _db.session.commit()
        ok("Métricas, histórico, logins commitados")

        # ── 14. RECALCULAR MÉTRICAS DE CLIENTES ──────────────────────────────
        print("\n🔄 [14/14] Recalculando métricas de clientes (total_compras, valor_gasto)...", flush=True)
        from app.models import ContaReceber as _CR
        for cli in clientes:
            vendas_cli = [v for v in vendas_todas if v.cliente_id == cli.id and v.status == "finalizada"]
            cli.total_compras    = len(vendas_cli)
            cli.valor_total_gasto = sum(float(v.total or 0) for v in vendas_cli)
            cli.ultima_compra    = max((v.data_venda for v in vendas_cli if v.data_venda), default=None)
            # saldo_devedor = soma das contas abertas (fiado não pago)
            contas_ab = _db.session.query(_CR).filter_by(cliente_id=cli.id, status="aberto").all()
            cli.saldo_devedor = sum(float(c.valor_atual or 0) for c in contas_ab)
        _db.session.commit()
        ok(f"{len(clientes)} clientes com métricas recalculadas")


        # ── RESUMO FINAL ─────────────────────────────────────────────────────
        title("SEED AIVEN CONCLUÍDA COM SUCESSO!")
        print(f"  Estabelecimentos : 2", flush=True)
        print(f"  Funcionários     : {len(funcionarios)}", flush=True)
        print(f"  Fornecedores     : {len(fornecedores)}", flush=True)
        print(f"  Categorias       : {len(CATEGORIAS) * 2}", flush=True)
        print(f"  Produtos         : {total_prods}", flush=True)
        print(f"  Clientes         : {len(clientes)}", flush=True)
        print(f"  Pedidos Compra   : {len(pedidos_compra)}", flush=True)
        print(f"  Vendas           : {vendas_criadas}", flush=True)
        print(f"  Tempo total      : {time.time() - inicio_vendas:.0f}s (vendas)", flush=True)
        print(flush=True)
        print("  CREDENCIAIS ADMIN:", flush=True)
        print("  Loja 1 → admin / admin123", flush=True)
        print("  Loja 2 → admin2 / admin123", flush=True)
        print("="*60, flush=True)


if __name__ == "__main__":
    run()
