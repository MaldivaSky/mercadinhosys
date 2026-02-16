"""
Seed de dados completo para o sistema ERP comercial (compativel com models.py atual).

Objetivos:
- Gerar dados realistas e completos para testar todas as funcionalidades do sistema
- Compativel com SQLite (localhost) e PostgreSQL (nuvem)
- Credenciais de teste: admin / admin123
- Todo produto DEVE ser oriundo de um pedido de compra (regra de negócio)
- Histórico de preços com tendências de alta e baixa para análise temporal

Uso:
  - `python seed_test.py --reset --local`   → Semear APENAS banco local (SQLite)
  - `python seed_test.py --reset --cloud`   → Semear APENAS banco nuvem (Neon/Postgres)
  - `python seed_test.py --reset --both`    → Semear AMBOS (local + nuvem)
  - `python seed_test.py --reset`           → Semear banco configurado (env vars)
  - `python seed_test.py`                   → Apenas preenche se estiver vazio

Automaticamente executado no Render pelo Start Command.
"""

from __future__ import annotations

import os
import sys
import argparse

# Carregar .env no início para AIVEN_DATABASE_URL/DATABASE_URL estar disponível com --cloud
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)
except Exception:
    pass
import random
import json
import hashlib
import time as time_module
from datetime import datetime, timedelta, date, time
from typing import List, Optional, Dict, Any
from decimal import Decimal

# Configurar encoding UTF-8 para evitar problemas de Unicode
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from sqlalchemy import text, exists

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from werkzeug.security import generate_password_hash

from app import create_app
from app.models import (
    db,
    Estabelecimento,
    Configuracao,
    Funcionario,
    Cliente,
    Fornecedor,
    CategoriaProduto,
    Produto,
    ProdutoLote,
    Venda,
    VendaItem,
    Pagamento,
    MovimentacaoEstoque,
    PedidoCompra,
    PedidoCompraItem,
    ContaPagar,
    ContaReceber,
    Despesa,
    LoginHistory,
    Caixa,
    MovimentacaoCaixa,
    DashboardMetrica,
    RelatorioAgendado,
    HistoricoPrecos,
    RegistroPonto,
    ConfiguracaoHorario,
    Beneficio,
    FuncionarioBeneficio,
    BancoHoras,
    JustificativaPonto,
)

DEFAULT_ESTABELECIMENTO_ID = 1


def _faker() -> Faker:
    """Retorna instância do Faker com seed fixa para consistência."""
    fake = Faker("pt_BR")
    random.seed(20250121)
    Faker.seed(20250121)
    return fake


def reset_database():
    """Destrói e recria o esquema do banco (SQLite/Postgres)."""
    print("[RESET] Iniciando RESET do banco de dados...")

    try:
        engine_name = db.engine.name
        print(f"  - Banco detectado: {engine_name}")

        # Estratégia híbrida para SQLite e PostgreSQL
        if engine_name == "sqlite":
            print("  - [SQLite] Recriando tabelas (DROP/CREATE)...")
            db.drop_all()
            db.create_all()
        else:
            # PostgreSQL - recriar todas as tabelas (DROP + CREATE) para garantir
            # schema igual ao models.py (ex.: coluna produtos.tipo). TRUNCATE não
            # adiciona colunas faltantes; create_all() não altera tabelas existentes.
            print("  - [PostgreSQL] Recriando tabelas (DROP ALL + CREATE ALL)...")
            db.drop_all()
            db.create_all()

        db.session.commit()
        print("✅ Banco limpo e estruturado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao resetar banco: {e}")
        db.session.rollback()
        raise


def ensure_estabelecimento(fake: Faker, estabelecimento_id: int = 1) -> Estabelecimento:
    """Garante que o estabelecimento exista."""
    est = db.session.get(Estabelecimento, estabelecimento_id)
    if est:
        return est

    nome_fantasia = f"Mercado {fake.city()} Center"
    razao_social = f"{nome_fantasia} COMÉRCIO DE ALIMENTOS LTDA"

    est = Estabelecimento(
        id=estabelecimento_id,
        nome_fantasia=nome_fantasia,
        razao_social=razao_social,
        cnpj=fake.cnpj(),
        inscricao_estadual=f"ISENTO",
        telefone=fake.phone_number(),
        email=fake.company_email(),
        cep=fake.postcode(),
        logradouro=fake.street_name(),
        numero=str(random.randint(1, 9999)),
        complemento="Sala 01",
        bairro="Centro",
        cidade=fake.city(),
        estado=fake.estado_sigla(),
        pais="Brasil",
        regime_tributario="SIMPLES NACIONAL",
        ativo=True,
        data_abertura=date.today() - timedelta(days=365 * 3),
        data_cadastro=datetime.now() - timedelta(days=180),
    )

    db.session.add(est)
    db.session.commit()
    return est


def ensure_configuracao(estabelecimento_id: int) -> Configuracao:
    """Garante configuração básica para o estabelecimento."""
    cfg = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
    if cfg:
        return cfg

    cfg = Configuracao(
        estabelecimento_id=estabelecimento_id,
        logo_url=None,
        cor_principal="#2563eb",
        emitir_nfe=False,
        emitir_nfce=True,
        desconto_maximo_funcionario=Decimal("10.00"),
        controlar_validade=True,
        alerta_estoque_minimo=True,
    )

    db.session.add(cfg)
    db.session.commit()
    return cfg


def seed_funcionarios(fake: Faker, estabelecimento_id: int) -> List[Funcionario]:
    """Cria funcionários ativos e histórico de demitidos."""
    print("👥 Criando funcionários (4 ativos + 25 demitidos)...")

    # FUNCIONÁRIOS ATIVOS (4)
    funcionarios_ativos_data = [
        {
            "nome": "Rafael Maldivas",
            "username": "admin",
            "cpf": "343.721.318-01",
            "data_nascimento": date(1987, 4, 28),
            "email": "admin@empresa.com",
            "cargo": "Proprietário",
            "data_admissao": date.today() - timedelta(days=730),  # 2 anos
            "salario_base": Decimal("8000.00"),
            "role": "ADMIN",
            "permissoes": {"pdv": True, "estoque": True, "compras": True, "financeiro": True, "configuracoes": True, "relatorios": True},
            "senha": "admin123",
        },
        {
            "nome": "Ana Paula Santos",
            "username": "gerente01",
            "cpf": "234.567.890-11",
            "data_nascimento": date(1985, 4, 12),
            "email": "ana@empresa.com",
            "cargo": "Gerente",
            "data_admissao": date.today() - timedelta(days=550),  # 1.5 anos
            "salario_base": Decimal("4500.00"),
            "role": "GERENTE",
            "permissoes": {"pdv": True, "estoque": True, "compras": True, "financeiro": True, "configuracoes": False, "relatorios": True},
            "senha": "gerente123",
        },
        {
            "nome": "Maria Silva",
            "username": "caixa01",
            "cpf": "456.789.012-33",
            "data_nascimento": date(1995, 2, 14),
            "email": "maria@empresa.com",
            "cargo": "Operador de Caixa",
            "data_admissao": date.today() - timedelta(days=365),  # 1 ano
            "salario_base": Decimal("2200.00"),
            "role": "FUNCIONARIO",
            "permissoes": {"pdv": True, "estoque": False, "compras": False, "financeiro": False, "configuracoes": False, "relatorios": False},
            "senha": "caixa123",
        },
        {
            "nome": "João Santos",
            "username": "estoque01",
            "cpf": "567.890.123-44",
            "data_nascimento": date(1998, 7, 22),
            "email": "joao@empresa.com",
            "cargo": "Repositor",
            "data_admissao": date.today() - timedelta(days=180),  # 6 meses
            "salario_base": Decimal("1800.00"),
            "role": "FUNCIONARIO",
            "permissoes": {"pdv": True, "estoque": True, "compras": False, "financeiro": False, "configuracoes": False, "relatorios": False},
            "senha": "estoque123",
        },
    ]

    # FUNCIONÁRIOS DEMITIDOS (6) - com histórico realista
    ex_funcionarios_data = [
        ("Roberto Oliveira", "345.678.901-22", date(1980, 6, 1), date.today() - timedelta(days=450), "Supervisor de Vendas", "Pediu demissão"),
        ("Fernanda Costa", "678.901.234-55", date(1988, 1, 10), date.today() - timedelta(days=200), "Operador de Caixa", "Demitida - faltas"),
        ("Pedro Almeida", "789.012.345-66", date(1992, 8, 5), date.today() - timedelta(days=300), "Repositor", "Pediu demissão"),
        ("Lucas Ferreira", "890.123.456-77", date(1994, 2, 1), date.today() - timedelta(days=550), "Repositor", "Demitido - desempenho"),
        ("Carla Rodrigues", "901.234.567-88", date(1991, 11, 15), date.today() - timedelta(days=100), "Operador de Caixa", "Pediu demissão"),
        ("André Souza", "012.345.678-99", date(1996, 1, 20), date.today() - timedelta(days=250), "Auxiliar Geral", "Demitido - experiência"),
    ]

    funcionarios = []
    
    # Criar funcionários ativos
    for func_data in funcionarios_ativos_data:
        existente = Funcionario.query.filter_by(
            estabelecimento_id=estabelecimento_id, username=func_data["username"]
        ).first()

        if existente:
            funcionarios.append(existente)
            continue

        f = Funcionario(
            estabelecimento_id=estabelecimento_id,
            nome=func_data["nome"],
            username=func_data["username"],
            cpf=func_data["cpf"],
            data_nascimento=func_data["data_nascimento"],
            telefone=fake.phone_number(),
            celular=fake.cellphone_number(),
            email=func_data["email"],
            cargo=func_data["cargo"],
            data_admissao=func_data["data_admissao"],
            salario_base=func_data["salario_base"],
            role=func_data["role"],
            permissoes_json=json.dumps(func_data["permissoes"]),
            ativo=True,
            cep=fake.postcode(),
            logradouro=fake.street_name(),
            numero=str(random.randint(1, 999)),
            bairro=fake.bairro(),
            cidade=fake.city(),
            estado=fake.estado_sigla(),
            pais="Brasil",
        )
        f.set_senha(func_data["senha"])
        db.session.add(f)
        funcionarios.append(f)

    # Criar ex-funcionários (demitidos)
    for nome, cpf, data_nasc, data_demissao, cargo, motivo in ex_funcionarios_data:
        username = nome.lower().replace(" ", "")[:10]
        
        existente = Funcionario.query.filter_by(
            estabelecimento_id=estabelecimento_id, cpf=cpf
        ).first()

        if existente:
            continue

        # Data de admissão: entre 1-3 anos antes da demissão
        dias_trabalhados = random.randint(180, 1095)
        data_admissao = data_demissao - timedelta(days=dias_trabalhados)

        ex_func = Funcionario(
            estabelecimento_id=estabelecimento_id,
            nome=nome,
            username=username,
            cpf=cpf,
            data_nascimento=data_nasc,
            telefone=fake.phone_number(),
            celular=fake.cellphone_number(),
            email=f"{username}@empresa.com",
            cargo=cargo,
            data_admissao=data_admissao,
            data_demissao=data_demissao,
            salario_base=Decimal(str(random.uniform(1800, 3500))),
            role="FUNCIONARIO",
            permissoes_json=json.dumps({"pdv": True, "estoque": True, "compras": False, "financeiro": False, "configuracoes": False, "relatorios": False}),
            ativo=False,
            cep=fake.postcode(),
            logradouro=fake.street_name(),
            numero=str(random.randint(1, 999)),
            bairro=fake.bairro(),
            cidade=fake.city(),
            estado=fake.estado_sigla(),
            pais="Brasil",
        )
        ex_func.set_senha("123456")
        db.session.add(ex_func)
        funcionarios.append(ex_func)

    db.session.commit()

    print(f"✅ {len(funcionarios_ativos_data)} funcionários ativos criados")
    print(f"✅ {len(ex_funcionarios_data)} ex-funcionários (histórico) criados")
    print(f"✅ Total: {len(funcionarios_ativos_data) + len(ex_funcionarios_data)} registros de RH")
    return funcionarios


def seed_clientes(fake: Faker, estabelecimento_id: int, n: int = 50) -> List[Cliente]:
    """Cria clientes de teste."""
    print("🧑‍🤝‍🧑 Criando clientes...")

    clientes = []
    for i in range(n):
        data_nascimento = fake.date_of_birth(minimum_age=18, maximum_age=80)
        total_compras = random.randint(0, 20)

        # Gerar complemento aleatório
        complementos = [
            "Apto 101",
            "Casa 2",
            "Sobrado",
            "Fundos",
            "Sala 3",
            "Bloco B",
            "",
        ]
        complemento = random.choice(complementos) if random.random() > 0.7 else ""

        c = Cliente(
            estabelecimento_id=estabelecimento_id,
            nome=fake.name(),
            cpf=fake.cpf(),
            rg=f"{fake.estado_sigla()}{random.randint(10000000, 99999999)}",
            data_nascimento=data_nascimento,
            telefone=fake.phone_number() if random.random() > 0.3 else None,
            celular=fake.cellphone_number(),
            email=fake.email() if random.random() > 0.2 else None,
            limite_credito=Decimal(str(round(random.uniform(500, 5000), 2))),
            saldo_devedor=Decimal("0.00"),
            ultima_compra=None,
            total_compras=total_compras,
            valor_total_gasto=Decimal(
                str(round(total_compras * random.uniform(50, 500), 2))
            ),
            ativo=random.random() > 0.1,  # 90% ativos
            observacoes=fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
            cep=fake.postcode(),
            logradouro=fake.street_name(),
            numero=str(random.randint(1, 9999)),
            complemento=complemento,
            bairro=fake.bairro(),
            cidade=fake.city(),
            estado=fake.estado_sigla(),
            pais="Brasil",
        )

        db.session.add(c)
        clientes.append(c)

    db.session.commit()
    print(f"✅ {len(clientes)} clientes criados")
    return clientes


def seed_fornecedores(
    fake: Faker, estabelecimento_id: int, n: int = 50
) -> List[Fornecedor]:
    """Cria fornecedores REAIS do Brasil."""
    print("🏭 Criando fornecedores reais do Brasil...")

    # Fornecedores REAIS do Brasil
    fornecedores_reais = [
        ("Ambev", "Ambev S/A", "07526847000148", "São Paulo", 7, "30 DIAS", "PREFERENCIAL"),
        ("Coca-Cola", "The Coca-Cola Company Brasil", "34028316000152", "São Paulo", 7, "30 DIAS", "PREFERENCIAL"),
        ("Nestlé", "Nestlé Brasil Ltda", "44477053000161", "São Paulo", 10, "30 DIAS", "PREFERENCIAL"),
        ("JBS", "JBS S/A", "17343969000164", "Goiás", 3, "15 DIAS", "PREFERENCIAL"),
        ("Seara", "Seara Alimentos S/A", "07526847000149", "Santa Catarina", 3, "15 DIAS", "PREFERENCIAL"),
        ("Perdigão", "Perdigão S/A", "07526847000150", "Santa Catarina", 3, "15 DIAS", "PREFERENCIAL"),
        ("Sadia", "Sadia S/A", "07526847000151", "Santa Catarina", 3, "15 DIAS", "PREFERENCIAL"),
        ("Friboi", "Friboi Frigorífico", "07526847000152", "Goiás", 2, "À VISTA", "REGULAR"),
        ("Itambé", "Itambé Alimentos", "17343969000165", "Minas Gerais", 5, "30 DIAS", "PREFERENCIAL"),
        ("Vigor", "Vigor Alimentos", "07526847000153", "São Paulo", 5, "30 DIAS", "PREFERENCIAL"),
        ("Danone", "Danone Brasil", "44477053000162", "São Paulo", 7, "30 DIAS", "PREFERENCIAL"),
        ("Yoplait", "Yoplait Brasil", "07526847000154", "São Paulo", 7, "30 DIAS", "PREFERENCIAL"),
        ("Pilão", "Pilão Alimentos", "07526847000155", "São Paulo", 10, "30 DIAS", "REGULAR"),
        ("Nescafé", "Nescafé Brasil", "44477053000163", "São Paulo", 10, "30 DIAS", "PREFERENCIAL"),
        ("Ypê", "Ypê Produtos de Limpeza", "07526847000156", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Veja", "Veja Produtos de Limpeza", "07526847000157", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Confort", "Confort Amaciante", "07526847000158", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Dove", "Dove Brasil", "07526847000159", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Clear", "Clear Xampus", "07526847000160", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Colgate", "Colgate-Palmolive", "07526847000161", "São Paulo", 15, "30 DIAS", "PREFERENCIAL"),
        ("Mondelez", "Mondelez Brasil", "07526847000162", "São Paulo", 10, "30 DIAS", "PREFERENCIAL"),
        ("Marilan", "Marilan Alimentos", "07526847000163", "São Paulo", 10, "30 DIAS", "REGULAR"),
        ("Tio João", "Tio João Alimentos", "07526847000164", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Camil", "Camil Alimentos", "07526847000165", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Renata", "Renata Alimentos", "07526847000166", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Liza", "Liza Óleos", "07526847000167", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Kicaldo", "Kicaldo Alimentos", "07526847000168", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Aviação", "Aviação Alimentos", "07526847000169", "São Paulo", 15, "30 DIAS", "REGULAR"),
        ("Neve", "Neve Papel Higiênico", "07526847000170", "São Paulo", 20, "30 DIAS", "REGULAR"),
        ("Omo", "Omo Detergentes", "07526847000171", "São Paulo", 20, "30 DIAS", "REGULAR"),
        ("Qboa", "Qboa Produtos", "07526847000172", "São Paulo", 20, "30 DIAS", "REGULAR"),
        ("Pullman", "Pullman Pão", "07526847000173", "São Paulo", 3, "À VISTA", "REGULAR"),
        ("Bimbo", "Bimbo Brasil", "07526847000174", "São Paulo", 3, "À VISTA", "PREFERENCIAL"),
        ("Heineken", "Heineken Brasil", "07526847000176", "São Paulo", 7, "30 DIAS", "PREFERENCIAL"),
        ("PepsiCo", "PepsiCo do Brasil", "07526847000177", "São Paulo", 7, "30 DIAS", "PREFERENCIAL"),
        ("Unilever", "Unilever Brasil", "07526847000178", "São Paulo", 10, "30 DIAS", "PREFERENCIAL"),
        ("P&G", "Procter & Gamble Brasil", "07526847000179", "São Paulo", 10, "30 DIAS", "PREFERENCIAL"),
        ("Johnson & Johnson", "J&J Brasil", "07526847000180", "São Paulo", 10, "30 DIAS", "REGULAR"),
        ("Bauducco", "Pandurata Alimentos", "07526847000181", "São Paulo", 7, "30 DIAS", "PREFERENCIAL"),
        ("Lactalis", "Lactalis do Brasil", "07526847000182", "Rio Grande do Sul", 7, "30 DIAS", "REGULAR"),
        ("Minerva Foods", "Minerva S/A", "07526847000183", "São Paulo", 5, "15 DIAS", "REGULAR"),
        ("Aurora Alimentos", "Aurora Coop", "07526847000184", "Santa Catarina", 5, "15 DIAS", "REGULAR"),
        ("BRF", "BRF S/A", "07526847000185", "Santa Catarina", 5, "15 DIAS", "PREFERENCIAL"),
        ("Copersucar", "Copersucar S/A", "07526847000186", "São Paulo", 10, "30 DIAS", "REGULAR"),
        ("Raízen", "Raízen Combustíveis", "07526847000187", "São Paulo", 7, "30 DIAS", "REGULAR"),
        ("Cargill", "Cargill Agrícola", "07526847000189", "São Paulo", 10, "30 DIAS", "REGULAR"),
        ("Bunge", "Bunge Alimentos", "07526847000190", "Santa Catarina", 10, "30 DIAS", "REGULAR"),
        ("ADM", "ADM do Brasil", "07526847000191", "São Paulo", 10, "30 DIAS", "REGULAR"),
        ("M. Dias Branco", "M. Dias Branco", "07526847000192", "Ceará", 10, "30 DIAS", "REGULAR"),
        ("Piracanjuba", "Laticínios Bela Vista", "07526847000193", "Goiás", 7, "30 DIAS", "REGULAR"),
    ]

    fornecedores = []
    for nome, razao, cnpj, cidade, prazo, pagamento, classificacao in fornecedores_reais[:n]:
        f = Fornecedor(
            estabelecimento_id=estabelecimento_id,
            nome_fantasia=nome,
            razao_social=razao,
            cnpj=cnpj,
            inscricao_estadual="ISENTO",
            telefone=fake.phone_number(),
            email=f"contato@{nome.lower().replace(' ', '')}.com.br",
            contato_nome=fake.name(),
            contato_telefone=fake.phone_number(),
            prazo_entrega=prazo,
            forma_pagamento=pagamento,
            classificacao=classificacao,
            total_compras=random.randint(5, 100),
            valor_total_comprado=Decimal(str(round(random.uniform(10000, 500000), 2))),
            ativo=True,
            cep="01310100",
            logradouro="Avenida Paulista",
            numero=str(random.randint(1000, 9999)),
            complemento="",
            bairro="Bela Vista",
            cidade=cidade,
            estado="SP",
            pais="Brasil",
        )
        db.session.add(f)
        fornecedores.append(f)

    db.session.commit()
    print(f"✅ {len(fornecedores)} fornecedores reais criados")
    return fornecedores


def seed_categorias_produto(
    fake: Faker, estabelecimento_id: int
) -> List[CategoriaProduto]:
    """Cria categorias de produtos completas para supermercado."""
    print("🏷️ Criando categorias de produtos...")

    categorias_data = [
        {"nome": "Bebidas", "descricao": "Refrigerantes, sucos, águas, cervejas"},
        {"nome": "Mercearia", "descricao": "Arroz, feijão, macarrão, óleo"},
        {"nome": "Frios e Laticínios", "descricao": "Queijos, iogurtes, manteiga"},
        {"nome": "Carnes", "descricao": "Bovinas, suínas, aves, peixes"},
        {"nome": "Congelados", "descricao": "Pizzas, lasanhas, sorvetes, vegetais congelados"},
        {"nome": "Açougue", "descricao": "Carnes frescas, aves, suínos, embutidos"},
        {"nome": "Higiene Pessoal", "descricao": "Sabonetes, shampoos, cremes"},
        {"nome": "Limpeza", "descricao": "Detergentes, desinfetantes, água sanitária"},
        {"nome": "Padaria", "descricao": "Pães, bolos, biscoitos"},
        {"nome": "Hortifrúti", "descricao": "Frutas, verduras, legumes"},
        {"nome": "Pet Shop", "descricao": "Rações, acessórios, higiene animal"},
    ]

    categorias = []
    for i, cat_data in enumerate(categorias_data, 1):
        c = CategoriaProduto(
            estabelecimento_id=estabelecimento_id,
            nome=cat_data["nome"],
            descricao=cat_data["descricao"],
            codigo=f"CAT{i:03d}",
            ativo=True,
        )

        db.session.add(c)
        categorias.append(c)

    db.session.commit()
    print(f"✅ {len(categorias)} categorias criadas")
    return categorias


def seed_produtos(
    fake: Faker,
    estabelecimento_id: int,
    categorias: List[CategoriaProduto],
    fornecedores: List[Fornecedor],
    n: int = 100,
) -> List[Produto]:
    """Cria produtos realistas com categorias."""
    print("📦 Criando produtos...")

    # PRODUTOS EXPANDIDOS - Mercado Brasileiro Real (150+ produtos)
    produtos_reais = [
        # ========== BEBIDAS (20 produtos) ==========
        ("Coca-Cola 2L", "Bebidas", "COC-001", "7894900010015", "Coca-Cola", 6.50, 10.90),
        ("Guaraná Antarctica 2L", "Bebidas", "GUA-001", "7891991000853", "Ambev", 5.80, 9.90),
        ("Pepsi 2L", "Bebidas", "PEP-001", "7894900530001", "PepsiCo", 6.20, 10.50),
        ("Fanta Laranja 2L", "Bebidas", "FAN-001", "7894900011005", "Coca-Cola", 6.00, 9.90),
        ("Sprite 2L", "Bebidas", "SPR-001", "7894900012002", "Coca-Cola", 6.00, 9.90),
        ("Água Mineral Crystal 500ml", "Bebidas", "AGU-001", "7892840822941", "Crystal", 1.20, 2.50),
        ("Suco Del Valle Laranja 1L", "Bebidas", "SUC-001", "7891098000251", "Del Valle", 3.50, 6.90),
        ("Suco Del Valle Uva 1L", "Bebidas", "SUC-002", "7891098000268", "Del Valle", 3.50, 6.90),
        ("Chá Matte Leão 1.5L", "Bebidas", "CHA-001", "7896005800015", "Matte Leão", 4.20, 7.50),
        ("Energético Red Bull 250ml", "Bebidas", "ENE-001", "9002490100015", "Red Bull", 8.50, 14.90),
        ("Cerveja Skol Lata 350ml", "Bebidas", "CER-001", "7891991010856", "Ambev", 2.80, 4.50),
        ("Cerveja Brahma Lata 350ml", "Bebidas", "CER-002", "7891991010863", "Ambev", 2.80, 4.50),
        ("Vinho Tinto Salton 750ml", "Bebidas", "VIN-001", "7896007200015", "Salton", 22.00, 35.90),
        ("Água de Coco Ducoco 1L", "Bebidas", "AGC-001", "7896094906015", "Ducoco", 5.50, 9.90),
        ("Suco Tang Laranja 25g", "Bebidas", "TAN-001", "7622300862015", "Mondelez", 1.20, 2.50),
        ("Refrigerante Dolly Guaraná 2L", "Bebidas", "DOL-001", "7896094901015", "Dolly", 4.50, 7.50),
        ("Achocolatado Toddynho 200ml", "Bebidas", "TOD-001", "7622300862022", "PepsiCo", 2.80, 4.90),
        ("Leite Fermentado Yakult 480ml", "Bebidas", "YAK-001", "7891095200015", "Yakult", 6.50, 11.90),
        ("Isotônico Gatorade 500ml", "Bebidas", "ISO-001", "7894900530018", "PepsiCo", 4.20, 7.50),
        ("Café Solúvel Nescafé 50g", "Bebidas", "CAF-SOL-001", "7891000100015", "Nestlé", 8.50, 14.90),

        # ========== MERCEARIA (35 produtos) ==========
        ("Arroz Tio João 5kg", "Mercearia", "ARR-001", "7896006741025", "Tio João", 24.00, 32.90),
        ("Arroz Camil 5kg", "Mercearia", "ARR-002", "7896006700000", "Camil", 23.50, 31.90),
        ("Feijão Carioca Camil 1kg", "Mercearia", "FEI-001", "7896079001015", "Camil", 7.50, 11.90),
        ("Feijão Preto Kicaldo 1kg", "Mercearia", "FEI-002", "7896079000000", "Kicaldo", 8.50, 12.90),
        ("Macarrão Renata Espaguete 500g", "Mercearia", "MAC-001", "7896051110223", "Renata", 3.50, 6.90),
        ("Óleo de Soja Liza 900ml", "Mercearia", "OLE-001", "7898909987042", "Liza", 6.50, 9.90),
        ("Açúcar União 1kg", "Mercearia", "ACU-001", "7891000053508", "União", 4.50, 6.90),
        ("Café Pilão 500g", "Mercearia", "CAF-001", "7896005800000", "Pilão", 14.50, 22.90),
        ("Sal Refinado Lebre 1kg", "Mercearia", "SAL-001", "7896000000000", "Distribuidor Local 2", 2.50, 4.20),
        ("Milho Pipoca Yoki 500g", "Mercearia", "PIPO-001", "7891000000000", "Yoki", 4.50, 7.80),
        ("Maionese Hellmann's 500g", "Mercearia", "MAIO-001", "7891000000001", "Unilever", 8.50, 13.90),
        ("Ketchup Heinz 397g", "Mercearia", "KET-001", "7891000000002", "Heinz", 10.50, 16.90),
        ("Leite Condensado Moça 395g", "Mercearia", "LEIT-001", "7891000000003", "Nestlé", 5.50, 8.90),
        ("Creme de Leite Nestlé 200g", "Mercearia", "CREM-001", "7891000000004", "Nestlé", 3.50, 5.90),
        ("Chocolate em Pó Nescau 400g", "Mercearia", "CHOC-001", "7891000000005", "Nestlé", 7.50, 11.90),
        ("Biscoito Cream Cracker Vitarella", "Mercearia", "BIS-002", "7891000000006", "M. Dias Branco", 3.50, 5.80),
        ("Macarrão Instantâneo Nissin", "Mercearia", "MIO-001", "7891000000007", "Distribuidor Local 5", 1.50, 2.90),
        ("Farinha de Trigo Dona Benta 1kg", "Mercearia", "FAR-001", "7896006700017", "J. Macêdo", 5.50, 8.90),
        ("Extrato de Tomate Elefante 340g", "Mercearia", "EXT-001", "7896036090015", "Cargill", 3.20, 5.50),
        ("Molho de Tomate Pomarola 520g", "Mercearia", "MOL-001", "7891150000018", "Unilever", 4.50, 7.50),
        ("Vinagre Castelo 750ml", "Mercearia", "VIN-002", "7896094900019", "Castelo", 3.80, 6.50),
        ("Azeite Português Andorinha 500ml", "Mercearia", "AZE-001", "5601012011015", "Sovena", 18.50, 29.90),
        ("Sardinha Gomes da Costa 125g", "Mercearia", "SAR-001", "7891167011015", "Gomes da Costa", 5.50, 9.50),
        ("Atum Ralado Gomes da Costa 170g", "Mercearia", "ATU-001", "7891167012015", "Gomes da Costa", 6.50, 11.90),
        ("Ervilha Quero 200g", "Mercearia", "ERV-001", "7896036091015", "Cargill", 2.80, 4.90),
        ("Milho Verde Quero 200g", "Mercearia", "MIL-001", "7896036092015", "Cargill", 2.80, 4.90),
        ("Catchup Heinz 200g", "Mercearia", "CAT-001", "7896036093015", "Heinz", 4.50, 7.50),
        ("Mostarda Hemmer 200g", "Mercearia", "MOS-001", "7896036094015", "Hemmer", 3.50, 5.90),
        ("Gelatina Royal Morango 85g", "Mercearia", "GEL-001", "7622300862029", "Mondelez", 2.20, 3.90),
        ("Fermento Royal 100g", "Mercearia", "FER-001", "7622300862036", "Mondelez", 4.50, 7.50),
        ("Aveia Quaker 500g", "Mercearia", "AVE-001", "7894900530025", "PepsiCo", 6.50, 11.50),
        ("Granola Nutry 1kg", "Mercearia", "GRA-001", "7896006700024", "Nutry", 12.50, 19.90),
        ("Amendoim Dori 500g", "Mercearia", "AME-001", "7896058200015", "Dori", 8.50, 14.90),
        ("Pipoca Microondas Yoki 100g", "Mercearia", "PIP-002", "7891000000015", "Yoki", 3.50, 5.90),
        ("Tempero Knorr Galinha 1kg", "Mercearia", "TEM-001", "7891150000025", "Knorr", 8.50, 14.50),

        # ========== FRIOS E LATICÍNIOS (15 produtos) ==========
        ("Leite Integral Italac 1L", "Frios e Laticínios", "LEI-001", "7898080640000", "Italac", 4.20, 6.50),
        ("Queijo Mussarela Fatiado kg", "Frios e Laticínios", "QUE-001", "7891000055502", "Itambé", 35.00, 59.90),
        ("Presunto Cozido Sadia kg", "Frios e Laticínios", "PRE-001", "7893000415101", "Sadia", 25.00, 45.90),
        ("Manteiga Aviação 200g", "Frios e Laticínios", "MAN-001", "7896051130000", "Aviação", 12.00, 19.90),
        ("Requeijão Vigor 200g", "Frios e Laticínios", "REQ-001", "7891000100000", "Vigor", 7.50, 12.90),
        ("Iogurte Nestlé Morango 1L", "Frios e Laticínios", "IOG-001", "7891072001308", "Nestlé", 9.90, 16.90),
        ("Iogurte Danone Natural 170g", "Frios e Laticínios", "IOG-002", "7891000000008", "Danone", 2.20, 3.80),
        ("Margarina Qualy 500g", "Frios e Laticínios", "MAR-001", "7891000000009", "BRF", 6.50, 10.90),
        ("Mortadela Perdigão 1kg", "Frios e Laticínios", "MOR-001", "7891000000010", "Perdigão", 15.50, 24.90),
        ("Queijo Prato Itambé kg", "Frios e Laticínios", "QUE-002", "7891000000011", "Itambé", 38.50, 62.00),
        ("Cream Cheese Philadelphia 150g", "Frios e Laticínios", "CRE-002", "7622300862043", "Mondelez", 8.50, 14.90),
        ("Leite Condensado Moça 395g", "Frios e Laticínios", "LEI-002", "7891000100022", "Nestlé", 5.50, 8.90),
        ("Salsicha Hot Dog Sadia 500g", "Frios e Laticínios", "SAL-002", "7893000415118", "Sadia", 8.50, 14.50),
        ("Bacon Fatiado Seara 250g", "Frios e Laticínios", "BAC-001", "7894904300015", "Seara", 12.50, 19.90),
        ("Queijo Coalho 500g", "Frios e Laticínios", "QUE-003", "7891000000018", "Tirolez", 18.50, 29.90),

        # ========== HIGIENE PESSOAL (20 produtos) ==========
        ("Sabonete Dove Original 90g", "Higiene Pessoal", "SAB-001", "7891150037605", "Dove", 3.50, 5.90),
        ("Pasta de Dente Colgate Total 12", "Higiene Pessoal", "PAS-001", "7891024035000", "Colgate", 6.50, 12.90),
        ("Papel Higiênico Neve 12un", "Higiene Pessoal", "PAP-001", "7891150000000", "Neve", 18.00, 29.90),
        ("Shampoo Pantene 400ml", "Higiene Pessoal", "SHA-002", "7891000000012", "P&G", 15.50, 25.90),
        ("Desodorante Rexona Aerosol", "Higiene Pessoal", "DESO-001", "7891000000013", "Unilever", 12.50, 18.90),
        ("Escova de Dente Oral-B", "Higiene Pessoal", "ESC-001", "7891000000014", "P&G", 8.50, 14.90),
        ("Fio Dental Colgate", "Higiene Pessoal", "FIO-001", "7891000000015", "Colgate", 5.50, 9.90),
        ("Absorvente Always", "Higiene Pessoal", "ABS-001", "7891000000016", "P&G", 7.50, 12.90),
        ("Condicionador Seda 325ml", "Higiene Pessoal", "CON-001", "7891150000032", "Unilever", 12.50, 19.90),
        ("Sabonete Líquido Protex 250ml", "Higiene Pessoal", "SAB-002", "7891024000033", "Colgate", 8.50, 14.50),
        ("Creme Dental Sensodyne 90g", "Higiene Pessoal", "PAS-002", "7891024000040", "GSK", 12.50, 21.90),
        ("Lenço Umedecido Huggies 48un", "Higiene Pessoal", "LEN-001", "7896004700015", "Kimberly", 9.50, 15.90),
        ("Fralda Pampers M 36un", "Higiene Pessoal", "FRA-002", "7891000000023", "P&G", 45.00, 69.90),
        ("Aparelho de Barbear Gillette", "Higiene Pessoal", "APA-001", "7891000000024", "Gillette", 18.50, 29.90),
        ("Creme de Barbear Gillette 200g", "Higiene Pessoal", "CRE-003", "7891000000025", "Gillette", 12.50, 19.90),
        ("Talco Johnson's 200g", "Higiene Pessoal", "TAL-001", "7891010000015", "Johnson's", 8.50, 14.50),
        ("Sabonete Líquido Dove 250ml", "Higiene Pessoal", "SAB-003", "7891150037612", "Dove", 12.50, 19.90),
        ("Desodorante Nivea Roll-on 50ml", "Higiene Pessoal", "DESO-002", "4005900000015", "Nivea", 9.50, 15.90),
        ("Shampoo Clear Men 400ml", "Higiene Pessoal", "SHA-003", "7891150054671", "Clear", 15.50, 25.90),
        ("Creme Hidratante Nivea 200ml", "Higiene Pessoal", "CRE-004", "4005900000022", "Nivea", 14.50, 23.90),

        # ========== LIMPEZA (15 produtos) ==========
        ("Detergente Ypê Neutro 500ml", "Limpeza", "DET-001", "7891024113405", "Ypê", 2.20, 3.90),
        ("Sabão em Pó Omo 800g", "Limpeza", "OMO-001", "7891150000001", "Omo", 12.50, 19.90),
        ("Amaciante Confort 1L", "Limpeza", "AMA-001", "7891150000002", "Confort", 14.50, 22.90),
        ("Água Sanitária Qboa 1L", "Limpeza", "SAN-001", "7896094908015", "Qboa", 5.50, 8.90),
        ("Desinfetante Pinho Sol 500ml", "Limpeza", "DES-001", "7891024000057", "Pinho Sol", 6.50, 10.90),
        ("Esponja de Aço Bombril 8un", "Limpeza", "ESP-001", "7896003700015", "Bombril", 3.50, 5.90),
        ("Sabão em Barra Ypê 5un", "Limpeza", "SAB-004", "7891024113412", "Ypê", 8.50, 13.90),
        ("Limpador Veja Multiuso 500ml", "Limpeza", "LIM-001", "7891150000064", "Veja", 7.50, 12.50),
        ("Alvejante Ypê 1L", "Limpeza", "ALV-001", "7891024113429", "Ypê", 6.50, 10.90),
        ("Sabão Líquido Omo 500ml", "Limpeza", "SAB-005", "7891150000071", "Omo", 14.50, 23.90),
        ("Lã de Aço Assolan 8un", "Limpeza", "LAA-001", "7896003700022", "Assolan", 3.50, 5.90),
        ("Detergente Ypê Limão 500ml", "Limpeza", "DET-002", "7891024113436", "Ypê", 2.20, 3.90),
        ("Desinfetante Lysoform 1L", "Limpeza", "DES-002", "7891024000064", "Lysoform", 12.50, 19.90),
        ("Saco de Lixo 100L 10un", "Limpeza", "SAC-001", "7896003700039", "Embalixo", 8.50, 14.50),
        ("Pano de Chão Perfex 5un", "Limpeza", "PAN-001", "7896003700046", "Perfex", 6.50, 10.90),

        # ========== CARNES (8 produtos) ==========
        ("Contra Filé Bovino kg", "Carnes", "CAR-001", None, "Friboi", 45.00, 69.90),
        ("Filé de Peito Frango kg", "Carnes", "FRA-001", None, "Seara", 18.00, 28.90),
        ("Linguiça Toscana Na Brasa kg", "Carnes", "LIN-001", None, "Perdigão", 16.00, 24.90),
        ("Picanha Bovina kg", "Carnes", "CAR-002", None, "Friboi", 55.00, 89.90),
        ("Costela Bovina kg", "Carnes", "CAR-003", None, "Friboi", 28.00, 45.90),
        ("Coxa e Sobrecoxa Frango kg", "Carnes", "FRA-003", None, "Seara", 12.00, 19.90),
        ("Carne Moída kg", "Carnes", "CAR-004", None, "Friboi", 22.00, 35.90),
        ("Linguiça Calabresa kg", "Carnes", "LIN-002", None, "Perdigão", 14.00, 22.90),

        # ========== HORTIFRÚTI (12 produtos) ==========
        ("Banana Prata kg", "Hortifrúti", "BAN-001", None, "Distribuidor Local 1", 4.50, 8.90),
        ("Tomate Italiano kg", "Hortifrúti", "TOM-001", None, "Distribuidor Local 2", 6.50, 12.90),
        ("Batata Lavada kg", "Hortifrúti", "BAT-001", None, "Distribuidor Local 3", 4.50, 8.90),
        ("Cebola kg", "Hortifrúti", "CEB-001", None, "Distribuidor Local 4", 3.50, 6.90),
        ("Ovos Brancos Dúzia", "Hortifrúti", "OVO-001", None, "Distribuidor Local 5", 8.00, 14.90),
        ("Maçã Argentina kg", "Hortifrúti", "MAC-002", None, "Distribuidor Local 1", 8.50, 15.90),
        ("Laranja Pera kg", "Hortifrúti", "LAR-001", None, "Distribuidor Local 1", 4.50, 8.50),
        ("Alface Crespa un", "Hortifrúti", "ALF-001", None, "Distribuidor Local 2", 2.50, 4.90),
        ("Cenoura kg", "Hortifrúti", "CEN-001", None, "Distribuidor Local 3", 3.50, 6.50),
        ("Limão Taiti kg", "Hortifrúti", "LIM-HOR-001", None, "Distribuidor Local 4", 4.50, 8.50),
        ("Abacaxi Pérola un", "Hortifrúti", "ABA-001", None, "Distribuidor Local 1", 5.50, 9.90),
        ("Melancia kg", "Hortifrúti", "MEL-001", None, "Distribuidor Local 1", 2.50, 4.90),

        # ========== CONGELADOS (10 produtos) ==========
        ("Pizza Sadia Mussarela 460g", "Congelados", "PIZ-001", "7893000415125", "Sadia", 12.50, 19.90),
        ("Lasanha Sadia Bolonhesa 600g", "Congelados", "LAS-001", "7893000415132", "Sadia", 18.50, 29.90),
        ("Nuggets Sadia 300g", "Congelados", "NUG-001", "7893000415149", "Sadia", 14.50, 22.90),
        ("Batata Pré-Frita McCain 1.5kg", "Congelados", "BAT-002", "7896004700022", "McCain", 16.50, 26.90),
        ("Sorvete Kibon Napolitano 2L", "Congelados", "SOR-001", "7891150000088", "Kibon", 22.50, 35.90),
        ("Hambúrguer Seara 672g", "Congelados", "HAM-001", "7894904300022", "Seara", 18.50, 29.90),
        ("Polpa de Açaí 1kg", "Congelados", "POL-001", "7896004700039", "Distribuidor Local 6", 24.50, 39.90),
        ("Empanado de Frango Sadia 300g", "Congelados", "EMP-001", "7893000415156", "Sadia", 16.50, 26.90),
        ("Pão de Queijo Forno de Minas 400g", "Congelados", "PAO-002", "7896004700046", "Forno de Minas", 12.50, 19.90),
        ("Strogonoff Perdigão 500g", "Congelados", "STR-001", "7891000000030", "Perdigão", 18.50, 29.90),

        # ========== PADARIA (8 produtos) ==========
        ("Pão Francês kg", "Padaria", "PAO-001", None, "Distribuidor Local 6", 12.00, 18.90),
        ("Biscoito Trakinas", "Padaria", "BIS-001", "7896000000001", "Mondelez", 3.50, 5.90),
        ("Bolo Pronto Pullman 250g", "Padaria", "BOL-001", "7896004700053", "Pullman", 8.50, 14.50),
        ("Pão de Forma Pullman 500g", "Padaria", "PAO-003", "7896004700060", "Pullman", 6.50, 10.90),
        ("Pão Integral Wickbold 400g", "Padaria", "PAO-004", "7891962000015", "Wickbold", 8.50, 14.50),
        ("Torrada Marilan 160g", "Padaria", "TOR-001", "7896003700053", "Marilan", 5.50, 9.50),
        ("Bisnaguinha Seven Boys 300g", "Padaria", "BIS-003", "7896004700077", "Seven Boys", 6.50, 10.90),
        ("Pão de Queijo Congelado 1kg", "Padaria", "PAO-005", "7896004700084", "Forno de Minas", 18.50, 29.90),
        
        # ========== PRODUTOS ADICIONAIS PARA COMPLETAR 200 (58 produtos) ==========
        
        # Bebidas Adicionais (10)
        ("Suco Maguary Laranja 1L", "Bebidas", "SUC-003", "7896004700091", "Maguary", 4.50, 7.90),
        ("Refrigerante Fanta Uva 2L", "Bebidas", "FAN-002", "7894900012019", "Coca-Cola", 6.00, 9.90),
        ("Água Tônica Schweppes 350ml", "Bebidas", "AGU-002", "7894900530032", "Schweppes", 3.50, 5.90),
        ("Cerveja Itaipava Lata 350ml", "Bebidas", "CER-003", "7896004700107", "Petrópolis", 2.50, 4.20),
        ("Leite Longa Vida Parmalat 1L", "Bebidas", "LEI-003", "7896004700114", "Parmalat", 4.50, 7.20),
        ("Achocolatado Nescau 200ml", "Bebidas", "ACH-002", "7891000100039", "Nestlé", 2.80, 4.90),
        ("Suco Ades Laranja 1L", "Bebidas", "SUC-004", "7896004700121", "Unilever", 5.50, 9.50),
        ("Refrigerante Guaraná Kuat 2L", "Bebidas", "GUA-002", "7894900012026", "Coca-Cola", 5.50, 9.50),
        ("Água de Coco Sococo 1L", "Bebidas", "AGC-002", "7896004700138", "Sococo", 5.50, 9.90),
        ("Cerveja Heineken Long Neck 330ml", "Bebidas", "CER-004", "8715428002391", "Heineken", 4.50, 7.90),
        
        # Mercearia Adicional (15)
        ("Biscoito Oreo 144g", "Mercearia", "BIS-004", "7622300862050", "Mondelez", 4.50, 7.50),
        ("Biscoito Passatempo 150g", "Mercearia", "BIS-005", "7896004700145", "Nestlé", 3.50, 5.90),
        ("Wafer Bauducco 140g", "Mercearia", "WAF-001", "7896004700152", "Bauducco", 3.80, 6.50),
        ("Achocolatado em Pó Toddy 400g", "Mercearia", "ACH-003", "7894900530049", "PepsiCo", 7.50, 12.50),
        ("Leite em Pó Ninho 400g", "Mercearia", "LEI-004", "7891000100046", "Nestlé", 18.50, 29.90),
        ("Cereal Sucrilhos Kellogg's 320g", "Mercearia", "CER-005", "7896004700169", "Kellogg's", 12.50, 19.90),
        ("Panetone Bauducco 500g", "Mercearia", "PAN-002", "7896004700176", "Bauducco", 15.50, 24.90),
        ("Goiabada Cascão 600g", "Mercearia", "GOI-001", "7896004700183", "Distribuidor Local 7", 8.50, 14.50),
        ("Doce de Leite Nestlé 400g", "Mercearia", "DOC-001", "7891000100053", "Nestlé", 9.50, 15.90),
        ("Mel Puro 500g", "Mercearia", "MEL-002", "7896004700190", "Distribuidor Local 8", 22.50, 35.90),
        ("Castanha de Caju 200g", "Mercearia", "CAS-001", "7896004700206", "Distribuidor Local 9", 18.50, 29.90),
        ("Amendoim Japonês 150g", "Mercearia", "AME-002", "7896058200022", "Dori", 5.50, 9.50),
        ("Barra de Cereal Nutry 3un", "Mercearia", "BAR-001", "7896006700031", "Nutry", 4.50, 7.50),
        ("Sopa Knorr Galinha 68g", "Mercearia", "SOP-001", "7891150000095", "Knorr", 3.50, 5.90),
        ("Tempero Sazon 60g", "Mercearia", "TEM-002", "7891150000101", "Knorr", 2.80, 4.90),
        
        # Frios e Laticínios Adicional (8)
        ("Iogurte Activia 170g", "Frios e Laticínios", "IOG-003", "7891000000037", "Danone", 2.50, 4.20),
        ("Petit Suisse Danoninho 320g", "Frios e Laticínios", "PET-001", "7891000000044", "Danone", 8.50, 14.50),
        ("Queijo Parmesão Ralado 50g", "Frios e Laticínios", "QUE-004", "7891000000051", "Kraft", 5.50, 9.50),
        ("Requeijão Catupiry 200g", "Frios e Laticínios", "REQ-002", "7896004700213", "Catupiry", 9.50, 15.90),
        ("Manteiga com Sal Aviação 200g", "Frios e Laticínios", "MAN-002", "7896051130017", "Aviação", 12.50, 20.50),
        ("Leite Fermentado Chamyto 480ml", "Frios e Laticínios", "LEI-005", "7891000000068", "Nestlé", 6.50, 11.50),
        ("Queijo Minas Frescal 500g", "Frios e Laticínios", "QUE-005", "7891000000075", "Tirolez", 16.50, 26.90),
        ("Peito de Peru Sadia 200g", "Frios e Laticínios", "PEI-001", "7893000415163", "Sadia", 14.50, 23.90),
        
        # Higiene Pessoal Adicional (8)
        ("Sabonete Líquido Palmolive 250ml", "Higiene Pessoal", "SAB-006", "7891024000071", "Colgate", 8.50, 14.50),
        ("Shampoo Elseve 400ml", "Higiene Pessoal", "SHA-004", "7896004700220", "L'Oréal", 16.50, 27.90),
        ("Condicionador Pantene 400ml", "Higiene Pessoal", "CON-002", "7891000000082", "P&G", 15.50, 25.90),
        ("Creme Dental Sensodyne Branqueador 90g", "Higiene Pessoal", "PAS-003", "7891024000088", "GSK", 14.50, 23.90),
        ("Enxaguante Bucal Listerine 500ml", "Higiene Pessoal", "ENX-001", "7891024000095", "Johnson's", 18.50, 29.90),
        ("Sabonete Líquido Nivea 250ml", "Higiene Pessoal", "SAB-007", "4005900000039", "Nivea", 12.50, 19.90),
        ("Desodorante Dove Roll-on 50ml", "Higiene Pessoal", "DESO-003", "7891150037629", "Dove", 9.50, 15.90),
        ("Creme para Pentear Seda 300ml", "Higiene Pessoal", "CRE-005", "7891150000118", "Unilever", 14.50, 23.90),
        
        # Limpeza Adicional (5)
        ("Sabão Líquido Ypê 500ml", "Limpeza", "SAB-LIM-001", "7891024113443", "Ypê", 12.50, 19.90),
        ("Limpador Multiuso Mr Músculo 500ml", "Limpeza", "LIM-002", "7891024000101", "SC Johnson", 8.50, 14.50),
        ("Amaciante Downy 1L", "Limpeza", "AMA-002", "7891000000099", "P&G", 16.50, 26.90),
        ("Esponja de Limpeza Scotch-Brite 3un", "Limpeza", "ESP-002", "7896004700237", "3M", 6.50, 10.90),
        ("Lustra Móveis Poliflor 200ml", "Limpeza", "LUS-001", "7896004700244", "Bombril", 8.50, 14.50),
        
        # Congelados Adicional (5)
        ("Batata Palito McCain 1kg", "Congelados", "BAT-003", "7896004700251", "McCain", 14.50, 23.90),
        ("Sorvete Kibon Chocolate 2L", "Congelados", "SOR-002", "7891150000125", "Kibon", 22.50, 35.90),
        ("Pizza Sadia Calabresa 460g", "Congelados", "PIZ-002", "7893000415170", "Sadia", 12.50, 19.90),
        ("Hambúrguer Perdigão 672g", "Congelados", "HAM-002", "7891000000105", "Perdigão", 18.50, 29.90),
        ("Polpa de Morango 1kg", "Congelados", "POL-002", "7896004700268", "Distribuidor Local 10", 18.50, 29.90),
        
        # Hortifrúti Adicional (3)
        ("Mamão Papaya kg", "Hortifrúti", "MAM-001", None, "Distribuidor Local 1", 5.50, 10.90),
        ("Uva Itália kg", "Hortifrúti", "UVA-001", None, "Distribuidor Local 1", 12.50, 19.90),
        ("Manga Palmer kg", "Hortifrúti", "MAN-003", None, "Distribuidor Local 1", 6.50, 12.50),
        
        # Pet Shop (4)
        ("Ração Pedigree Carne 1kg", "Pet Shop", "RAC-001", "7896004700275", "Mars", 18.50, 29.90),
        ("Ração Whiskas Peixe 1kg", "Pet Shop", "RAC-002", "7896004700282", "Mars", 16.50, 26.90),
        ("Areia Higiênica Pipicat 4kg", "Pet Shop", "ARE-001", "7896004700299", "Distribuidor Local 11", 22.50, 35.90),
        ("Petisco Pedigree Dentastix 110g", "Pet Shop", "PET-002", "7896004700305", "Mars", 12.50, 19.90),
        
        # Produtos Finais para completar 200 (2)
        ("Refrigerante Sprite Zero 2L", "Bebidas", "SPR-002", "7894900012033", "Coca-Cola", 6.50, 10.50),
        ("Biscoito Recheado Bono 126g", "Mercearia", "BIS-006", "7896004700312", "Nestlé", 3.80, 6.50),
    ]

    # Mapear categorias por nome
    categorias_map = {c.nome: c for c in categorias}

    produtos = []
    
    # Mapa de marca -> fornecedor_id para garantir que cada produto tenha o fornecedor correto
    marca_fornecedor_map = {}
    for fornecedor in fornecedores:
        # Mapear nomes de marcas conhecidas para fornecedores
        if fornecedor.nome_fantasia.lower() in [
            "coca-cola", "ambev", "heineken", "crystal", "del valle", 
            "tio joão", "camil", "kicaldo", "renata", "liza", "união", 
            "pilão", "italac", "itambé", "sadia", "aviação", "vigor", 
            "nestlé", "dove", "colgate", "neve", "omo", "confort", "qboa",
            "friboi", "seara", "perdigão", "pullman", "mondelez", "pepsico",
            "unilever", "brf", "danone", "m. dias branco", "minerva foods",
            "aurora alimentos", "p&g", "yoki", "heinz", "salton", "ducoco",
            "dolly", "yakult", "j. macêdo", "cargill", "castelo", "sovena",
            "gomes da costa", "hemmer", "nutry", "dori", "knorr", "tirolez",
            "gsk", "kimberly", "gillette", "johnson's", "nivea", "pinho sol",
            "bombril", "veja", "assolan", "lysoform", "embalixo", "perfex",
            "mccain", "kibon", "forno de minas", "wickbold", "seven boys"
        ]:
            marca_fornecedor_map[fornecedor.nome_fantasia.lower()] = fornecedor.id
    
    # Lista de produtos reais conhecidos no Brasil
    # The previous produtos_reais list was replaced with the expanded one above.

    used_codes = set()
    for p in produtos_reais:
        if p[2]: used_codes.add(p[2])

    # Gerar mais produtos até chegar a n=200
    while len(produtos_reais) < n:
        cat = random.choice(categorias)
        nome_gen = f"{fake.word().capitalize()} {fake.word().capitalize()} {random.choice(['Premium', 'Tradicional', 'Plus', 'Eco'])}"
        
        while True:
            codigo_gen = f"{cat.nome[:3].upper()}-{random.randint(1000, 9999)}"
            if codigo_gen not in used_codes:
                used_codes.add(codigo_gen)
                break
                
        marca_gen = random.choice([f.nome_fantasia for f in fornecedores])
        custo_gen = round(random.uniform(2.0, 50.0), 2)
        venda_gen = round(custo_gen * random.uniform(1.3, 1.8), 2)
        produtos_reais.append((nome_gen, cat.nome, codigo_gen, fake.ean13(), marca_gen, custo_gen, venda_gen))

    for i, (
        nome,
        categoria_nome,
        codigo,
        codigo_barras,
        marca,
        preco_custo,
        preco_venda,
    ) in enumerate(produtos_reais):
        categoria = categorias_map.get(categoria_nome)
        if not categoria:
            continue

        # Determinar fornecedor_id baseado na marca
        # 🔥 REGRA: Todo produto DEVE ter um fornecedor (obrigatório para pedidos de compra)
        fornecedor_id = None
        if marca:
            # Tentar encontrar o fornecedor pela marca
            marca_lower = marca.lower()
            if marca_lower in marca_fornecedor_map:
                fornecedor_id = marca_fornecedor_map[marca_lower]
            else:
                # Se não encontrar, procurar um fornecedor com nome similar
                for fornecedor in fornecedores:
                    if fornecedor.nome_fantasia.lower() == marca_lower:
                        fornecedor_id = fornecedor.id
                        break
                # Se ainda não encontrou, usar o primeiro fornecedor disponível
                if not fornecedor_id and fornecedores:
                    fornecedor_id = fornecedores[0].id
        else:
            # Se não tem marca, usar um fornecedor aleatório
            if fornecedores:
                fornecedor_id = random.choice(fornecedores).id
        
        # 🔥 SAFETY NET: Se AINDA não tem fornecedor, atribuir o primeiro da lista
        # Isso garante que NENHUM produto fique sem fornecedor (requisito para pedidos de compra)
        if not fornecedor_id and fornecedores:
            fornecedor_id = fornecedores[0].id
        
        if not fornecedor_id:
            print(f"  ⚠️ ERRO CRÍTICO: Produto '{nome}' sem fornecedor disponível! Ignorando.")
            continue

        # Gerar dados variados
        quantidade = random.randint(500, 1000)  # Aumentado de 20-200 para 500-1000
        quantidade_minima = max(10, quantidade // 10)  # Reduzido para 10% em vez de 25%
        # Garantir custo positivo para evitar divisão por zero
        preco_custo_val = float(preco_custo) if preco_custo and float(preco_custo) > 0 else 1.0
        preco_venda_val = float(preco_venda)
        
        margem = ((preco_venda_val - preco_custo_val) / preco_custo_val) * 100
        # Limitar margem para caber no Numeric(5, 2) das models (max 999.99)
        margem = max(0, min(999.99, margem))

        # 🔥 DATA DE VALIDADE e LOTE: Serão definidos pelos ProdutoLote (pedidos de compra)
        # O Produto.data_validade reflete a validade do lote MAIS PRÓXIMO de vencer (FIFO)
        # O Produto.lote reflete o numero_lote correspondente
        # Inicialmente None → preenchidos em seed_pedidos_compra e seed_lotes_reabastecimento

        p = Produto(
            estabelecimento_id=estabelecimento_id,
            categoria_id=categoria.id,
            fornecedor_id=fornecedor_id,
            codigo_barras=codigo_barras or fake.ean13(),
            codigo_interno=codigo,
            nome=nome,
            descricao=f"{nome} - {marca if marca else 'Produto fresco'}",
            marca=marca if marca else None,
            fabricante=marca if marca else "Fabricante Próprio",
            tipo=categoria.nome,
            unidade_medida=random.choice(["UN", "KG", "L", "CX"]),
            quantidade=0,  # IMPORTANTE: Estoque vem de pedidos de compra
            quantidade_minima=random.randint(20, 50),
            preco_custo=Decimal(str(round(preco_custo_val, 2))),
            preco_venda=Decimal(str(round(preco_venda_val, 2))),
            margem_lucro=Decimal(str(round(margem, 2))),
            ncm="".join([str(random.randint(0, 9)) for _ in range(8)]),
            origem=0,
            total_vendido=0.0,
            quantidade_vendida=0,
            classificacao_abc=random.choice(["A", "B", "C"]),
            controlar_validade=True,
            data_validade=None,  # 🔥 Será definido pelo ProdutoLote (FIFO)
            lote=None,           # 🔥 Será definido pelo ProdutoLote (pedido de compra)
            imagem_url=None,
            ativo=True,
        )

        db.session.add(p)
        produtos.append(p)

    db.session.commit()
    print(f"✅ {len(produtos)} produtos criados")
    return produtos


def seed_vendas(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    clientes: List[Cliente],
    produtos: List[Produto],
    dias_passados: int = 90,  # Reduzido de 180 para 90 dias
    vendas_por_dia: tuple = (2, 5),  # Reduzido de (3, 8) para (2, 5)
    neon_safe: bool = False,  # True = batches menores + delay para Neon free tier
):
    """Cria vendas realistas com itens e pagamentos.
    
    🔥 INCLUI TENDÊNCIA DE CRESCIMENTO:
    - Dias mais antigos têm MENOS vendas (multiplicador menor)
    - Dias mais recentes têm MAIS vendas (multiplicador maior)
    - Isso garante que a métrica de crescimento no dashboard seja realista (~15-25%)
    
    🔥 DEADLOCK: Ordena produtos por ID antes de atualizar (ordem consistente de locks).
    🔥 NEON FREE TIER: neon_safe=True → BATCH_SIZE=10, delay 10s entre batches.
    """
    print("🧾 Criando vendas (com tendência de crescimento)...")

    vendas_criadas = 0
    hoje = date.today()
    BATCH_SIZE = 10 if neon_safe else 20  # Neon free tier: batches menores
    DELAY_BETWEEN_BATCHES = 10.0 if neon_safe else 0.0  # 10s para Neon

    # Distribuição horária de vendas (8h às 21h - horário comercial estendido)
    horarios_pico = [
        (8, 1),   # Abertura
        (9, 2),
        (10, 3),
        (11, 4),
        (12, 5),  # Pico almoço
        (13, 3),
        (14, 2),
        (15, 2),
        (16, 3),
        (17, 4),
        (18, 5),  # Pico saída do trabalho
        (19, 4),
        (20, 3),
        (21, 1),  # Fechamento
    ]

    for dia_offset in range(dias_passados, -1, -1):
        data_venda = hoje - timedelta(days=dia_offset)

        # 🔥 TENDÊNCIA DE CRESCIMENTO: Multiplicador que aumenta ao longo do tempo
        # Fator de 0.6 (passado distante) a 1.4 (dias recentes) = ~130% de variação
        # Isso gera ~20% de crescimento entre períodos adjacentes de 30 dias
        progresso = 1.0 - (dia_offset / max(dias_passados, 1))  # 0.0 (passado) → 1.0 (hoje)
        multiplicador_tendencia = 0.6 + (progresso * 0.8)  # 0.6 → 1.4

        # Menos vendas em finais de semana
        if data_venda.weekday() >= 5:  # Sábado ou domingo
            min_vendas, max_vendas = max(1, vendas_por_dia[0] - 2), max(
                3, vendas_por_dia[1] - 3
            )
        else:
            min_vendas, max_vendas = vendas_por_dia

        # 🔥 Aplicar tendência ao número de vendas do dia
        base_vendas = random.randint(min_vendas, max_vendas)
        num_vendas = max(1, round(base_vendas * multiplicador_tendencia))

        for venda_num in range(num_vendas):
            # Escolher horário baseado na distribuição
            hora, peso = random.choice(horarios_pico)
            minuto = random.randint(0, 59)
            segundo = random.randint(0, 59)

            data_hora_venda = datetime.combine(
                data_venda, time(hour=hora, minute=minuto, second=segundo)
            )

            # Escolher funcionário e cliente
            funcionario = random.choice(funcionarios)
            cliente = (
                random.choice([None] + clientes) if random.random() > 0.3 else None
            )

            venda = Venda(
                estabelecimento_id=estabelecimento_id,
                cliente_id=cliente.id if cliente else None,
                funcionario_id=funcionario.id,
                codigo=f"V{data_venda.strftime('%Y%m%d')}{venda_num+1:03d}",
                subtotal=Decimal("0.00"),
                desconto=Decimal("0.00"),
                total=Decimal("0.00"),
                forma_pagamento=random.choice(
                    ["dinheiro", "pix", "cartao_debito", "cartao_credito"]
                ),
                valor_recebido=Decimal("0.00"),
                troco=Decimal("0.00"),
                status="finalizada",
                quantidade_itens=0,
                observacoes=(
                    fake.text(max_nb_chars=50) if random.random() > 0.8 else None
                ),
                data_venda=data_hora_venda,
            )
            db.session.add(venda)
            db.session.flush()

            # Criar itens da venda - 🔥 Mais itens em dias recentes
            base_itens = random.randint(1, 8)
            num_itens = max(1, round(base_itens * multiplicador_tendencia))
            subtotal = Decimal("0.00")

            if random.random() < 0.80:
                num_produtos_populares = max(1, len(produtos) // 5)
                produtos_populares = produtos[:num_produtos_populares]
                produtos_venda = random.choices(produtos_populares, k=min(num_itens, len(produtos_populares)))
            else:
                produtos_venda = random.sample(produtos, min(num_itens, len(produtos)))

            # 🔥 ANTI-DEADLOCK: Ordenar por ID para ordem consistente de locks no PostgreSQL
            produtos_venda = sorted(set(produtos_venda), key=lambda p: p.id)

            for produto in produtos_venda:
                quantidade = random.randint(1, 3)
                preco_unitario = Decimal(str(produto.preco_venda))
                desconto_item = Decimal("0.00")

                # Aplicar desconto ocasional
                if random.random() > 0.85:
                    desconto_item = preco_unitario * Decimal("0.1")  # 10% de desconto

                total_item = (preco_unitario * Decimal(str(quantidade))) - desconto_item

                item = VendaItem(
                    venda_id=venda.id,
                    produto_id=produto.id,
                    produto_nome=produto.nome,
                    produto_codigo=produto.codigo_interno or produto.codigo_barras,
                    produto_unidade=produto.unidade_medida,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    desconto=desconto_item,
                    total_item=total_item,
                    custo_unitario=Decimal(str(produto.preco_custo)),
                    margem_item=Decimal(
                        str(
                            round(
                                (
                                    (float(preco_unitario) - float(produto.preco_custo))
                                    / float(produto.preco_custo)
                                    * 100
                                ),
                                2,
                            )
                        )
                    ),
                )

                db.session.add(item)

                # Atualizar estoque - usar Decimal
                produto.quantidade -= quantidade
                produto.quantidade_vendida = (produto.quantidade_vendida or 0) + quantidade
                produto.total_vendido = float(Decimal(str(produto.total_vendido or 0)) + total_item)
                produto.ultima_venda = data_hora_venda

                # Criar movimentação de estoque
                mov = MovimentacaoEstoque(
                    estabelecimento_id=estabelecimento_id,
                    produto_id=produto.id,
                    venda_id=venda.id,
                    funcionario_id=funcionario.id,
                    tipo="saida",
                    quantidade=quantidade,
                    quantidade_anterior=produto.quantidade + quantidade,
                    quantidade_atual=produto.quantidade,
                    custo_unitario=Decimal(str(produto.preco_custo)),
                    valor_total=Decimal(str(produto.preco_custo)) * Decimal(str(quantidade)),
                    motivo="Venda",
                    observacoes=None,
                    created_at=data_hora_venda,
                )
                db.session.add(mov)

                subtotal += total_item

            # Calcular totais da venda
            desconto_venda = Decimal("0.00")
            if random.random() > 0.9:  # 10% de chance de desconto na venda
                desconto_venda = subtotal * Decimal(str(random.uniform(0.05, 0.15)))

            total_venda = subtotal - desconto_venda

            venda.subtotal = subtotal
            venda.desconto = desconto_venda
            venda.total = total_venda
            venda.quantidade_itens = num_itens
            venda.valor_recebido = total_venda
            venda.troco = Decimal("0.00")

            # Criar pagamento
            pagamento = Pagamento(
                venda_id=venda.id,
                estabelecimento_id=estabelecimento_id,
                forma_pagamento=venda.forma_pagamento,
                valor=total_venda,
                troco=Decimal("0.00"),
                status="aprovado",
                data_pagamento=data_hora_venda,
                observacoes=None,
            )
            db.session.add(pagamento)

            # Atualizar cliente
            if cliente:
                cliente.total_compras = (cliente.total_compras or 0) + 1
                cliente.valor_total_gasto = Decimal(str(cliente.valor_total_gasto or 0)) + total_venda
                cliente.ultima_compra = data_hora_venda

            vendas_criadas += 1

            # 🔥 Commit em lotes para evitar timeout/deadlock (Neon free tier)
            if vendas_criadas % BATCH_SIZE == 0:
                db.session.commit()
                if DELAY_BETWEEN_BATCHES > 0:
                    print(f"   ⏳ {vendas_criadas} vendas... aguardando {int(DELAY_BETWEEN_BATCHES)}s (Neon free tier)")
                    time_module.sleep(DELAY_BETWEEN_BATCHES)
                    # Keepalive + retry: após sleep o Neon pode ter suspendido. Forçar conexão viva antes do próximo batch.
                    for t in range(5):
                        try:
                            db.session.execute(text("SELECT 1"))
                            db.session.commit()
                            break
                        except Exception:
                            db.session.rollback()
                            try:
                                db.engine.dispose()
                            except Exception:
                                pass
                            if t == 4:
                                raise
                            wait = 20 * (t + 1)
                            print(f"   ⚠️ Reconectando... (tentativa {t+1}/5, aguardando {wait}s)")
                            time_module.sleep(wait)

    # Commit final do que restou
    db.session.commit()
    print(f"✅ {vendas_criadas} vendas criadas")
    return vendas_criadas


def seed_garantir_vendas_todos_produtos(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    clientes: List[Cliente],
    produtos: List[Produto],
    neon_safe: bool = False,
):
    """Garante que TODOS os produtos tenham pelo menos uma venda registrada.
    Mantém a distribuição de Pareto. neon_safe=True: batches menores + delay 10s para Neon."""
    print("🔄 Garantindo que todos os produtos tenham vendas com distribuição de Pareto...")

    produtos_sem_venda = [p for p in produtos if not p.ultima_venda or p.quantidade_vendida == 0]
    
    if not produtos_sem_venda:
        print(f"✅ Todos os {len(produtos)} produtos já têm vendas")
        return

    print(f"⚠️  {len(produtos_sem_venda)} produtos sem vendas - criando vendas para eles...")

    hoje = date.today()
    funcionario = random.choice([f for f in funcionarios if f.ativo])
    vendas_batch = 0
    BATCH_SIZE = 10 if neon_safe else 20
    DELAY_BETWEEN_BATCHES = 10.0 if neon_safe else 0.0

    # Dividir produtos em grupos para distribuição de Pareto
    num_produtos_populares = max(1, len(produtos) // 5)  # 20% dos produtos
    
    for idx, produto in enumerate(produtos_sem_venda):
        # Determinar quantas vendas este produto deve ter (Pareto)
        if idx < num_produtos_populares:
            # Produtos populares: 5-15 vendas
            num_vendas = random.randint(5, 15)
        else:
            # Produtos menos populares: 1-3 vendas
            num_vendas = random.randint(1, 3)
        
        for venda_num in range(num_vendas):
            # Criar uma venda para este produto
            data_venda = hoje - timedelta(days=random.randint(1, 180))
            hora = random.randint(8, 20)
            minuto = random.randint(0, 59)
            data_hora_venda = datetime.combine(data_venda, time(hour=hora, minute=minuto))
            
            cliente = random.choice([None] + clientes) if random.random() > 0.3 else None
            
            venda = Venda(
                estabelecimento_id=estabelecimento_id,
                cliente_id=cliente.id if cliente else None,
                funcionario_id=funcionario.id,
                codigo=f"V{data_venda.strftime('%Y%m%d')}{random.randint(1000, 9999):04d}",
                subtotal=Decimal("0.00"),
                desconto=Decimal("0.00"),
                total=Decimal("0.00"),
                forma_pagamento=random.choice(["dinheiro", "pix", "cartao_debito", "cartao_credito"]),
                valor_recebido=Decimal("0.00"),
                troco=Decimal("0.00"),
                status="finalizada",
                quantidade_itens=1,
                data_venda=data_hora_venda,
            )
            
            db.session.add(venda)
            db.session.flush()
            
            # Criar item da venda
            quantidade = random.randint(1, 5)
            preco_unitario = Decimal(str(produto.preco_venda))
            total_item = preco_unitario * Decimal(str(quantidade))
            
            item = VendaItem(
                venda_id=venda.id,
                produto_id=produto.id,
                produto_nome=produto.nome,
                produto_codigo=produto.codigo_interno or produto.codigo_barras,
                produto_unidade=produto.unidade_medida,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                desconto=Decimal("0.00"),
                total_item=total_item,
                custo_unitario=Decimal(str(produto.preco_custo)),
                margem_item=Decimal(str(round(((float(preco_unitario) - float(produto.preco_custo)) / float(produto.preco_custo) * 100), 2))),
            )
            
            db.session.add(item)
            
            # Atualizar estoque e métricas do produto
            # 🔥 CORREÇÃO: Decrementar estoque (estava faltando, causando inconsistência)
            produto.quantidade -= quantidade
            produto.quantidade_vendida = (produto.quantidade_vendida or 0) + quantidade
            produto.total_vendido = float(Decimal(str(produto.total_vendido or 0)) + total_item)
            produto.ultima_venda = data_hora_venda
            
            # Criar movimentação (vinculada à venda, NÃO a pedido de compra)
            mov = MovimentacaoEstoque(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                venda_id=venda.id,
                funcionario_id=funcionario.id,
                tipo="saida",
                quantidade=quantidade,
                quantidade_anterior=produto.quantidade + quantidade,
                quantidade_atual=produto.quantidade,
                custo_unitario=Decimal(str(produto.preco_custo)),
                valor_total=Decimal(str(produto.preco_custo)) * Decimal(str(quantidade)),
                motivo="Venda (garantia de dados)",
            )
            db.session.add(mov)
            
            # Criar pagamento
            pagamento = Pagamento(
                venda_id=venda.id,
                estabelecimento_id=estabelecimento_id,
                forma_pagamento=venda.forma_pagamento,
                valor=total_item,
                troco=Decimal("0.00"),
                status="aprovado",
                data_pagamento=data_hora_venda,
            )
            db.session.add(pagamento)
            
            # Atualizar cliente
            if cliente:
                cliente.total_compras = (cliente.total_compras or 0) + 1
                cliente.valor_total_gasto = Decimal(str(cliente.valor_total_gasto or 0)) + total_item
                cliente.ultima_compra = data_hora_venda
            
            venda.subtotal = total_item
            venda.total = total_item
            venda.valor_recebido = total_item

            vendas_batch += 1
            if vendas_batch % BATCH_SIZE == 0:
                db.session.commit()
                if DELAY_BETWEEN_BATCHES > 0:
                    print(f"   ⏳ {vendas_batch} vendas (garantia)... aguardando {int(DELAY_BETWEEN_BATCHES)}s (Neon free tier)")
                    time_module.sleep(DELAY_BETWEEN_BATCHES)
                    for t in range(5):
                        try:
                            db.session.execute(text("SELECT 1"))
                            db.session.commit()
                            break
                        except Exception:
                            db.session.rollback()
                            try:
                                db.engine.dispose()
                            except Exception:
                                pass
                            if t == 4:
                                raise
                            wait = 20 * (t + 1)
                            print(f"   ⚠️ Reconectando... (tentativa {t+1}/5, aguardando {wait}s)")
                            time_module.sleep(wait)

    db.session.commit()
    print(f"✅ {len(produtos_sem_venda)} produtos agora têm vendas registradas com distribuição de Pareto")


def seed_pedidos_compra(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    fornecedores: List[Fornecedor],
    produtos: List[Produto],
):
    """
    🔥 REGRA DE NEGÓCIO: TODO produto só pode ter estoque se vier de um pedido de compra.
    Nenhum produto pode existir no sistema sem pelo menos 1 pedido de compra associado.
    """
    print("📦 Criando pedidos de compra para TODOS os produtos...")
    
    hoje = date.today()
    pedidos_criados = 0
    lotes_criados = 0
    boletos_criados = 0
    produtos_com_pedido = set()  # Rastrear quais produtos receberam pedido
    
    # 🔥 SAFETY NET: Corrigir produtos órfãos (sem fornecedor ou fornecedor inválido)
    fornecedor_fallback = fornecedores[0] if fornecedores else None
    if not fornecedor_fallback:
        print("  ❌ ERRO CRÍTICO: Nenhum fornecedor disponível! Impossível criar pedidos de compra.")
        return
    
    produtos_orfaos = 0
    for p in produtos:
        if not p.fornecedor_id:
            p.fornecedor_id = fornecedor_fallback.id
            produtos_orfaos += 1
        else:
            # Verificar se o fornecedor_id realmente existe
            forn_existe = db.session.get(Fornecedor, p.fornecedor_id)
            if not forn_existe:
                p.fornecedor_id = fornecedor_fallback.id
                produtos_orfaos += 1
    
    if produtos_orfaos > 0:
        db.session.commit()
        print(f"  ⚠️ {produtos_orfaos} produtos estavam sem fornecedor válido → atribuídos ao fornecedor '{fornecedor_fallback.nome_fantasia}'")
    
    # Agrupar produtos por fornecedor (agora TODOS têm fornecedor válido)
    produtos_por_fornecedor = {}
    for p in produtos:
        if p.fornecedor_id not in produtos_por_fornecedor:
            produtos_por_fornecedor[p.fornecedor_id] = []
        produtos_por_fornecedor[p.fornecedor_id].append(p)
    
    funcionarios_validos = [f for f in funcionarios if f.cargo != "Operador de Caixa"]
    if not funcionarios_validos:
        funcionarios_validos = funcionarios  # Fallback: qualquer funcionário
    
    for forn_id, produtos_forn in produtos_por_fornecedor.items():
        fornecedor = db.session.get(Fornecedor, forn_id)
        if not fornecedor:
            # Isso NÃO deveria acontecer após o safety net acima, mas por segurança:
            print(f"  ❌ Fornecedor ID={forn_id} não encontrado mesmo após correção! {len(produtos_forn)} produtos afetados.")
            continue
            
        funcionario = random.choice(funcionarios_validos)
        data_pedido = hoje - timedelta(days=random.randint(60, 120))
        data_previsao = data_pedido + timedelta(days=fornecedor.prazo_entrega)

        pedido = PedidoCompra(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=fornecedor.id,
            funcionario_id=funcionario.id,
            numero_pedido=f"PC{data_pedido.strftime('%Y%m%d')}{pedidos_criados+1:03d}",
            data_pedido=data_pedido,
            status="recebido",
            data_recebimento=data_previsao,
            subtotal=Decimal("0.00"),
            total=Decimal("0.00"),
            condicao_pagamento=fornecedor.forma_pagamento,
            numero_nota_fiscal=fake.ean13(),
        )
        db.session.add(pedido)
        db.session.flush()
        
        subtotal_pedido = Decimal("0.00")
        for produto in produtos_forn:
            quantidade = random.randint(100, 200)
            preco_compra = produto.preco_custo * Decimal("0.9")
            total_item = preco_compra * Decimal(str(quantidade))
            
            item = PedidoCompraItem(
                pedido_id=pedido.id,
                produto_id=produto.id,
                produto_nome=produto.nome,
                quantidade_solicitada=quantidade,
                quantidade_recebida=quantidade,
                preco_unitario=preco_compra,
                total_item=total_item,
                status="recebido",
            )
            db.session.add(item)
            subtotal_pedido += total_item
            
            # Movimentação de estoque vinculada ao pedido de compra
            quantidade_anterior = produto.quantidade
            produto.quantidade += quantidade
            mov = MovimentacaoEstoque(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                pedido_compra_id=pedido.id,
                funcionario_id=funcionario.id,
                tipo="entrada",
                quantidade=quantidade,
                quantidade_anterior=quantidade_anterior,
                quantidade_atual=produto.quantidade,
                custo_unitario=preco_compra,
                valor_total=total_item,
                motivo="Entrada via Pedido de Compra",
                created_at=data_pedido,
            )
            db.session.add(mov)
            
            # 🔥 Lote vinculado ao pedido de compra com validade REALISTA para FIFO e alertas
            # Distribuição de validade:
            #   ~8% já vencidos (testes de alerta de vencido)
            #   ~10% vencendo em até 7 dias (alerta CRÍTICO)
            #   ~15% vencendo em 8-30 dias (alerta MÉDIO)
            #   ~67% validade normal (60-365 dias)
            sorteio_validade = random.random()
            if sorteio_validade < 0.08:
                # JÁ VENCIDO: entre 1 e 30 dias atrás
                dias_validade = random.randint(-30, -1)
            elif sorteio_validade < 0.18:
                # CRÍTICO: vence em 1-7 dias
                dias_validade = random.randint(1, 7)
            elif sorteio_validade < 0.33:
                # MÉDIO: vence em 8-30 dias
                dias_validade = random.randint(8, 30)
            else:
                # NORMAL: validade de 60-365 dias
                dias_validade = random.randint(60, 365)
            
            data_validade_lote = hoje + timedelta(days=dias_validade)
            
            lote = ProdutoLote(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                pedido_compra_id=pedido.id,
                fornecedor_id=fornecedor.id,
                numero_lote=f"L{data_pedido.strftime('%Y%m')}{lotes_criados+1:04d}",
                quantidade_inicial=quantidade,
                quantidade=quantidade,
                data_validade=data_validade_lote,
                data_entrada=data_pedido,
                preco_custo_unitario=preco_compra,
                ativo=True,
            )
            db.session.add(lote)
            lotes_criados += 1
            
            # 🔥 Sincronizar Produto.data_validade com o lote mais próximo de vencer (FIFO)
            if not produto.data_validade or data_validade_lote < produto.data_validade:
                produto.data_validade = data_validade_lote
                produto.lote = lote.numero_lote
            
            # Registrar que este produto recebeu pedido de compra
            produtos_com_pedido.add(produto.id)

        pedido.subtotal = subtotal_pedido
        pedido.total = subtotal_pedido
        fornecedor.total_compras += 1
        fornecedor.valor_total_comprado += subtotal_pedido
        pedidos_criados += 1
        
        # 🔥 Gerar conta a pagar com STATUS VARIADO (não tudo como "pago")
        prazo_dias = random.choice([15, 21, 28, 30, 45, 60])
        data_vencimento = data_pedido + timedelta(days=prazo_dias)
        dias_ate_vencimento = (data_vencimento - hoje).days
        
        # Status baseado na idade do boleto:
        # - Vencimento já passou: 70% pago, 20% pago com atraso, 10% vencido (aberto)
        # - Vencimento futuro: 100% aberto (ainda não venceu)
        if dias_ate_vencimento < -30:
            # Bem antigo
            sorteio = random.random()
            if sorteio < 0.90:
                status_bol = "pago"
                data_pgto = data_vencimento + timedelta(days=random.randint(0, 10))
            else:
                status_bol = "aberto"  # Esquecido!
                data_pgto = None
        elif dias_ate_vencimento < 0:
            # Venceu recentemente
            sorteio = random.random()
            if sorteio < 0.60:
                status_bol = "pago"
                data_pgto = data_vencimento + timedelta(days=random.randint(0, 5))
            else:
                status_bol = "aberto"  # Vencido
                data_pgto = None
        elif dias_ate_vencimento <= 7:
            # Vence em breve (0-7 dias)
            status_bol = "aberto"
            data_pgto = None
        else:
            # Vence daqui a mais de 7 dias
            status_bol = "aberto"
            data_pgto = None
        
        boleto = ContaPagar(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=fornecedor.id,
            pedido_compra_id=pedido.id,
            numero_documento=f"FAT{pedido.numero_pedido}",
            tipo_documento="duplicata",
            valor_original=pedido.total,
            valor_pago=pedido.total if status_bol == "pago" else Decimal("0"),
            valor_atual=Decimal("0") if status_bol == "pago" else pedido.total,
            data_emissao=data_pedido,
            data_vencimento=data_vencimento,
            data_pagamento=data_pgto,
            status=status_bol,
            forma_pagamento=random.choice(["transferencia", "boleto", "pix"]),
            observacoes=f"Pedido {pedido.numero_pedido} - {fornecedor.nome_fantasia}",
        )
        db.session.add(boleto)
        boletos_criados += 1
    
    db.session.commit()
    
    # 🔥 VERIFICAÇÃO FINAL: Garantir que NENHUM produto ficou sem pedido de compra
    produtos_sem_pedido = [p for p in produtos if p.id not in produtos_com_pedido]
    if produtos_sem_pedido:
        print(f"  ❌ ALERTA: {len(produtos_sem_pedido)} produtos ficaram sem pedido de compra!")
        for p in produtos_sem_pedido[:10]:
            print(f"     - [{p.id}] {p.nome} (fornecedor_id={p.fornecedor_id})")
        raise RuntimeError(
            f"VIOLAÇÃO DE REGRA DE NEGÓCIO: {len(produtos_sem_pedido)} produtos sem pedido de compra! "
            "Todo produto DEVE ser oriundo de um pedido de compra."
        )
    
    # Verificar que nenhum produto tem estoque sem movimentação
    produtos_estoque_zero = [p for p in produtos if p.quantidade <= 0]
    if produtos_estoque_zero:
        print(f"  ⚠️ {len(produtos_estoque_zero)} produtos com estoque zerado após pedidos de compra")
    
    print(f"✅ {pedidos_criados} pedidos de compra criados | {lotes_criados} lotes | {boletos_criados} boletos")
    print(f"✅ VERIFICADO: {len(produtos_com_pedido)}/{len(produtos)} produtos têm pedido de compra (100%)")


def seed_lotes_reabastecimento(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    fornecedores: List[Fornecedor],
    produtos: List[Produto],
):
    """
    🔥 Simula reabastecimentos ao longo do tempo (múltiplos lotes por produto).
    
    Essencial para testar:
    - FIFO real (qual lote vender primeiro?)
    - Alertas granulares por lote (um lote vencendo, outro OK)
    - Rastreabilidade de lotes diferentes do mesmo produto
    
    ~40% dos produtos recebem 1-3 lotes adicionais com datas de validade variadas.
    """
    print("📦 Criando lotes de reabastecimento (FIFO com múltiplos lotes por produto)...")
    
    hoje = date.today()
    lotes_criados = 0
    produtos_reabastecidos = 0
    pedidos_criados = 0
    
    funcionarios_validos = [f for f in funcionarios if f.cargo != "Operador de Caixa"]
    if not funcionarios_validos:
        funcionarios_validos = funcionarios
    
    # ~40% dos produtos recebem reabastecimento
    produtos_para_reabastecer = random.sample(
        produtos,
        k=min(len(produtos), max(1, int(len(produtos) * 0.40)))
    )
    
    # Agrupar por fornecedor para criar pedidos de compra realistas
    produtos_por_fornecedor = {}
    for p in produtos_para_reabastecer:
        if p.fornecedor_id not in produtos_por_fornecedor:
            produtos_por_fornecedor[p.fornecedor_id] = []
        produtos_por_fornecedor[p.fornecedor_id].append(p)
    
    for forn_id, produtos_forn in produtos_por_fornecedor.items():
        fornecedor = db.session.get(Fornecedor, forn_id)
        if not fornecedor:
            continue
        
        funcionario = random.choice(funcionarios_validos)
        
        # 1-3 pedidos de reabastecimento por fornecedor, espaçados no tempo
        num_pedidos_reab = random.randint(1, 3)
        
        for pedido_num in range(num_pedidos_reab):
            # Datas de pedido distribuídas: 10-50 dias atrás
            data_pedido = hoje - timedelta(days=random.randint(10, 50))
            data_previsao = data_pedido + timedelta(days=fornecedor.prazo_entrega)
            
            pedido = PedidoCompra(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=fornecedor.id,
                funcionario_id=funcionario.id,
                numero_pedido=f"PCREAB{data_pedido.strftime('%Y%m%d')}{pedidos_criados+1:03d}",
                data_pedido=data_pedido,
                status="recebido",
                data_recebimento=data_previsao,
                subtotal=Decimal("0.00"),
                total=Decimal("0.00"),
                condicao_pagamento=fornecedor.forma_pagamento,
                numero_nota_fiscal=fake.ean13(),
            )
            db.session.add(pedido)
            db.session.flush()
            
            subtotal_pedido = Decimal("0.00")
            
            # Selecionar um subconjunto dos produtos deste fornecedor
            produtos_pedido = random.sample(
                produtos_forn,
                k=min(len(produtos_forn), random.randint(1, max(1, len(produtos_forn) // 2)))
            )
            
            for produto in produtos_pedido:
                quantidade = random.randint(30, 80)
                preco_compra = produto.preco_custo * Decimal("0.9")
                total_item = preco_compra * Decimal(str(quantidade))
                
                item = PedidoCompraItem(
                    pedido_id=pedido.id,
                    produto_id=produto.id,
                    produto_nome=produto.nome,
                    quantidade_solicitada=quantidade,
                    quantidade_recebida=quantidade,
                    preco_unitario=preco_compra,
                    total_item=total_item,
                    status="recebido",
                )
                db.session.add(item)
                subtotal_pedido += total_item
                
                # Movimentação de estoque
                quantidade_anterior = produto.quantidade
                produto.quantidade += quantidade
                mov = MovimentacaoEstoque(
                    estabelecimento_id=estabelecimento_id,
                    produto_id=produto.id,
                    pedido_compra_id=pedido.id,
                    funcionario_id=funcionario.id,
                    tipo="entrada",
                    quantidade=quantidade,
                    quantidade_anterior=quantidade_anterior,
                    quantidade_atual=produto.quantidade,
                    custo_unitario=preco_compra,
                    valor_total=total_item,
                    motivo="Reabastecimento via Pedido de Compra",
                    created_at=data_pedido,
                )
                db.session.add(mov)
                
                # 🔥 Lote com validade variada para testar FIFO e alertas
                sorteio = random.random()
                if sorteio < 0.12:
                    dias_val = random.randint(-15, -1)   # JÁ VENCIDO
                elif sorteio < 0.25:
                    dias_val = random.randint(1, 7)      # CRÍTICO: 1-7 dias
                elif sorteio < 0.42:
                    dias_val = random.randint(8, 30)     # MÉDIO: 8-30 dias
                else:
                    dias_val = random.randint(60, 300)    # NORMAL
                
                data_validade_lote = hoje + timedelta(days=dias_val)
                
                lote = ProdutoLote(
                    estabelecimento_id=estabelecimento_id,
                    produto_id=produto.id,
                    pedido_compra_id=pedido.id,
                    fornecedor_id=fornecedor.id,
                    numero_lote=f"LREAB{data_pedido.strftime('%Y%m%d')}{lotes_criados+1:04d}",
                    quantidade_inicial=quantidade,
                    quantidade=quantidade,
                    data_validade=data_validade_lote,
                    data_entrada=data_pedido,
                    preco_custo_unitario=preco_compra,
                    ativo=True,
                )
                db.session.add(lote)
                lotes_criados += 1
                
                # Sincronizar Produto.data_validade com o lote MAIS PRÓXIMO de vencer (FIFO)
                if not produto.data_validade or data_validade_lote < produto.data_validade:
                    produto.data_validade = data_validade_lote
                    produto.lote = lote.numero_lote
                
                produtos_reabastecidos += 1
            
            pedido.subtotal = subtotal_pedido
            pedido.total = subtotal_pedido
            fornecedor.total_compras += 1
            fornecedor.valor_total_comprado += subtotal_pedido
            pedidos_criados += 1
    
    db.session.commit()
    
    # Estatísticas
    lotes_vencidos = db.session.query(ProdutoLote).filter(
        ProdutoLote.estabelecimento_id == estabelecimento_id,
        ProdutoLote.data_validade < hoje,
        ProdutoLote.ativo == True,
    ).count()
    
    lotes_criticos = db.session.query(ProdutoLote).filter(
        ProdutoLote.estabelecimento_id == estabelecimento_id,
        ProdutoLote.data_validade.between(hoje, hoje + timedelta(days=7)),
        ProdutoLote.ativo == True,
    ).count()
    
    lotes_medios = db.session.query(ProdutoLote).filter(
        ProdutoLote.estabelecimento_id == estabelecimento_id,
        ProdutoLote.data_validade.between(hoje + timedelta(days=8), hoje + timedelta(days=30)),
        ProdutoLote.ativo == True,
    ).count()
    
    print(f"✅ {lotes_criados} lotes de reabastecimento criados via {pedidos_criados} pedidos de compra")
    print(f"   🔴 {lotes_vencidos} lotes JÁ VENCIDOS (alerta imediato)")
    print(f"   🟠 {lotes_criticos} lotes vencendo em 1-7 dias (alerta CRÍTICO)")
    print(f"   🟡 {lotes_medios} lotes vencendo em 8-30 dias (alerta MÉDIO)")
    print(f"   📦 {produtos_reabastecidos} reabastecimentos para {len(produtos_para_reabastecer)} produtos")


def seed_historico_precos(
    fake: Faker,
    estabelecimento_id: int,
    produtos: List[Produto],
    funcionarios: List[Funcionario],
    dias_historico: int = 180,
):
    """
    🔥 Gera histórico realista de alterações de preços ao longo do tempo.
    
    Simula cenários reais de mercado:
    - Reajuste de fornecedor (custo sobe → venda sobe)
    - Promoção temporária (venda cai, custo mantém)
    - Fim de promoção (venda volta ao normal)
    - Correção inflacionária (ambos sobem)
    - Negociação com fornecedor (custo cai → repasse parcial ao consumidor)
    - Aumento de demanda (venda sobe, custo mantém)
    
    O sistema pode então identificar:
    - Produtos com ALTA de preço recente
    - Produtos com BAIXA de preço recente
    - Tendência de preço por período
    - Impacto na margem de lucro
    """
    print("📈 Criando histórico de alterações de preços...")
    
    hoje = date.today()
    registros_criados = 0
    produtos_com_alta = 0
    produtos_com_baixa = 0
    produtos_estavel = 0
    
    # Funcionários que podem alterar preços (gerentes/admin)
    funcionarios_gestores = [
        f for f in funcionarios 
        if f.cargo in ("Gerente", "Administrador", "Supervisor")
    ]
    if not funcionarios_gestores:
        funcionarios_gestores = funcionarios[:3]  # Fallback
    
    # Motivos e cenários de alteração de preço
    cenarios = [
        {
            "motivo": "Reajuste do fornecedor",
            "tipo": "alta_custo",
            "custo_pct": (0.03, 0.15),   # Custo sobe 3-15%
            "venda_pct": (0.03, 0.12),    # Venda sobe 3-12% (repasse parcial)
            "peso": 25,
        },
        {
            "motivo": "Promoção temporária",
            "tipo": "baixa_venda",
            "custo_pct": (0, 0),           # Custo mantém
            "venda_pct": (-0.20, -0.05),   # Venda cai 5-20%
            "peso": 20,
        },
        {
            "motivo": "Fim de promoção",
            "tipo": "alta_venda",
            "custo_pct": (0, 0),           # Custo mantém
            "venda_pct": (0.05, 0.20),     # Venda volta 5-20%
            "peso": 15,
        },
        {
            "motivo": "Correção inflacionária",
            "tipo": "alta_ambos",
            "custo_pct": (0.02, 0.08),     # Custo sobe 2-8%
            "venda_pct": (0.02, 0.08),     # Venda sobe 2-8%
            "peso": 15,
        },
        {
            "motivo": "Negociação com fornecedor",
            "tipo": "baixa_custo",
            "custo_pct": (-0.10, -0.03),   # Custo cai 3-10%
            "venda_pct": (-0.05, 0.0),     # Venda cai 0-5% (repasse parcial)
            "peso": 10,
        },
        {
            "motivo": "Aumento de demanda",
            "tipo": "alta_venda",
            "custo_pct": (0, 0),           # Custo mantém
            "venda_pct": (0.03, 0.10),     # Venda sobe 3-10%
            "peso": 8,
        },
        {
            "motivo": "Concorrência - redução estratégica",
            "tipo": "baixa_venda",
            "custo_pct": (0, 0),           # Custo mantém
            "venda_pct": (-0.15, -0.03),   # Venda cai 3-15%
            "peso": 7,
        },
    ]
    
    pesos = [c["peso"] for c in cenarios]
    
    # 60-70% dos produtos terão alterações de preço
    produtos_alterados = random.sample(
        produtos, 
        k=min(len(produtos), max(1, int(len(produtos) * random.uniform(0.60, 0.70))))
    )
    
    for produto in produtos_alterados:
        # Cada produto tem 1-5 alterações ao longo do período
        num_alteracoes = random.randint(1, 5)
        
        # Gerar datas distribuídas ao longo do período
        datas_alteracao = sorted([
            hoje - timedelta(days=random.randint(1, dias_historico))
            for _ in range(num_alteracoes)
        ])
        
        # Preço base do produto (custo e venda originais vindo do pedido de compra)
        custo_atual = float(produto.preco_custo)
        venda_atual = float(produto.preco_venda)
        
        # Rastrear se o preço final ficou maior ou menor que o original
        venda_original = venda_atual
        
        for data_alt in datas_alteracao:
            # Selecionar cenário
            cenario = random.choices(cenarios, weights=pesos, k=1)[0]
            funcionario = random.choice(funcionarios_gestores)
            
            # Calcular variações
            custo_min, custo_max = cenario["custo_pct"]
            venda_min, venda_max = cenario["venda_pct"]
            
            variacao_custo = random.uniform(custo_min, custo_max) if custo_min != custo_max else 0.0
            variacao_venda = random.uniform(venda_min, venda_max) if venda_min != venda_max else 0.0
            
            # Valores anteriores
            custo_anterior = custo_atual
            venda_anterior = venda_atual
            
            # Aplicar variações
            custo_novo = max(0.01, custo_atual * (1 + variacao_custo))
            venda_novo = max(custo_novo * 1.05, venda_atual * (1 + variacao_venda))  # Venda nunca abaixo de custo+5%
            
            # Calcular margens
            margem_anterior = ((venda_anterior - custo_anterior) / custo_anterior * 100) if custo_anterior > 0 else 0
            margem_nova = ((venda_novo - custo_novo) / custo_novo * 100) if custo_novo > 0 else 0
            
            # Limitar margem ao Numeric(5,2) do banco (max 999.99)
            margem_anterior = max(-99.99, min(999.99, margem_anterior))
            margem_nova = max(-99.99, min(999.99, margem_nova))
            
            # Gerar observação contextualizada
            observacoes = None
            if cenario["tipo"] == "alta_custo":
                observacoes = f"Fornecedor reajustou em {abs(variacao_custo)*100:.1f}%. Repasse parcial ao consumidor."
            elif cenario["tipo"] == "baixa_venda" and "Promoção" in cenario["motivo"]:
                dias_promo = random.randint(7, 30)
                observacoes = f"Promoção válida por {dias_promo} dias. Desconto de {abs(variacao_venda)*100:.1f}%."
            elif cenario["tipo"] == "baixa_custo":
                observacoes = f"Renegociação bem-sucedida. Economia de {abs(variacao_custo)*100:.1f}% no custo."
            elif "Concorrência" in cenario["motivo"]:
                observacoes = "Redução para acompanhar preço da concorrência local."
            
            data_hora = datetime.combine(data_alt, time(
                hour=random.randint(8, 17),
                minute=random.randint(0, 59)
            ))
            
            historico = HistoricoPrecos(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                funcionario_id=funcionario.id,
                preco_custo_anterior=Decimal(str(round(custo_anterior, 2))),
                preco_venda_anterior=Decimal(str(round(venda_anterior, 2))),
                margem_anterior=Decimal(str(round(margem_anterior, 2))),
                preco_custo_novo=Decimal(str(round(custo_novo, 2))),
                preco_venda_novo=Decimal(str(round(venda_novo, 2))),
                margem_nova=Decimal(str(round(margem_nova, 2))),
                motivo=cenario["motivo"],
                observacoes=observacoes,
                data_alteracao=data_hora,
            )
            db.session.add(historico)
            registros_criados += 1
            
            # Atualizar preços atuais para a próxima iteração
            custo_atual = custo_novo
            venda_atual = venda_novo
        
        # 🔥 Atualizar o produto com o preço FINAL (último da cadeia)
        produto.preco_custo = Decimal(str(round(custo_atual, 2)))
        produto.preco_venda = Decimal(str(round(venda_atual, 2)))
        nova_margem = ((venda_atual - custo_atual) / custo_atual * 100) if custo_atual > 0 else 0
        produto.margem_lucro = Decimal(str(round(min(999.99, max(0, nova_margem)), 2)))
        
        # Classificar tendência
        variacao_total = ((venda_atual - venda_original) / venda_original * 100) if venda_original > 0 else 0
        if variacao_total > 2:
            produtos_com_alta += 1
        elif variacao_total < -2:
            produtos_com_baixa += 1
        else:
            produtos_estavel += 1
    
    db.session.commit()
    
    print(f"✅ {registros_criados} registros de histórico de preços criados para {len(produtos_alterados)} produtos")
    print(f"   📈 {produtos_com_alta} produtos com ALTA de preço (tendência de alta)")
    print(f"   📉 {produtos_com_baixa} produtos com BAIXA de preço (tendência de baixa)")
    print(f"   ➡️  {produtos_estavel} produtos com preço estável (variação < 2%)")
    print(f"   📊 {len(produtos) - len(produtos_alterados)} produtos sem alteração de preço no período")


def seed_despesas(fake: Faker, estabelecimento_id: int, fornecedores: List[Fornecedor]):
    """
    🔥 MÓDULO FINANCEIRO ERP - Despesas integradas com Contas a Pagar.
    
    Regras de negócio:
    1. Despesas fixas recorrentes GERAM ContaPagar (boleto) mensal com vencimento definido
    2. Boletos antigos são marcados como pagos
    3. Boletos recentes ficam com status variado (pagos, abertos, vencidos)
    4. Sistema deve alertar boletos próximos do vencimento
    5. Despesas problemáticas são registradas para análise de corte
    6. Toda despesa com forma_pagamento='boleto' TEM uma ContaPagar correspondente
    """
    print("💸 Criando despesas + contas a pagar (módulo financeiro ERP)...")

    hoje = date.today()
    despesas = []
    boletos_criados = 0
    boletos_pagos = 0
    boletos_abertos = 0
    boletos_vencidos = 0
    
    # ═══════════════════════════════════════════════════════════
    # DESPESAS FIXAS RECORRENTES → GERAM BOLETO (ContaPagar)
    # ═══════════════════════════════════════════════════════════
    despesas_fixas = [
        {"descricao": "Aluguel",             "categoria": "Aluguel",          "valor": 2500.00, "dia_vencimento": 10, "fornecedor_nome": "Imobiliária"},
        {"descricao": "Energia Elétrica",     "categoria": "Energia",          "valor": 800.00,  "dia_vencimento": 15, "fornecedor_nome": "Concessionária"},
        {"descricao": "Água e Esgoto",        "categoria": "Água",             "valor": 300.00,  "dia_vencimento": 20, "fornecedor_nome": "Saneamento"},
        {"descricao": "Internet/Telefonia",   "categoria": "Telecomunicações", "valor": 250.00,  "dia_vencimento": 5,  "fornecedor_nome": "Telecom"},
        {"descricao": "Contabilidade",        "categoria": "Contábil",         "valor": 600.00,  "dia_vencimento": 10, "fornecedor_nome": "Escritório Contábil"},
        {"descricao": "Seguro do Imóvel",     "categoria": "Seguros",          "valor": 180.00,  "dia_vencimento": 25, "fornecedor_nome": "Seguradora"},
        {"descricao": "Alvará/Licenças",      "categoria": "Impostos",         "valor": 120.00,  "dia_vencimento": 15, "fornecedor_nome": "Prefeitura"},
        {"descricao": "Sistema de Câmeras",   "categoria": "Segurança",        "valor": 150.00,  "dia_vencimento": 1,  "fornecedor_nome": "Segurança"},
        {"descricao": "Manutenção Ar-Condicionado", "categoria": "Manutenção", "valor": 200.00,  "dia_vencimento": 20, "fornecedor_nome": "Climatização"},
        {"descricao": "Software ERP (licença)", "categoria": "TI",            "valor": 99.90,   "dia_vencimento": 5,  "fornecedor_nome": "TI"},
    ]
    
    # Mapa de fornecedores por nome aproximado
    fornecedor_map = {}
    for f in fornecedores:
        fornecedor_map[f.id] = f
    fornecedor_fallback = fornecedores[0] if fornecedores else None
    
    for desp_data in despesas_fixas:
        # Selecionar fornecedor aleatório para esta despesa fixa
        forn = random.choice(fornecedores) if fornecedores else None
        
        # Criar despesa + boleto para cada mês (últimos 6 meses + mês atual)
        for mes_offset in range(6, -1, -1):
            ano = hoje.year
            mes = hoje.month - mes_offset
            while mes <= 0:
                mes += 12
                ano -= 1
            
            # Data da despesa (primeiro dia útil do mês)
            data_despesa = date(ano, mes, 1)
            
            # Data de vencimento do boleto
            dia_venc = min(desp_data["dia_vencimento"], 28)
            data_vencimento = date(ano, mes, dia_venc)
            
            # Valor com variação mensal realista (±10%)
            valor = Decimal(str(round(desp_data["valor"] * random.uniform(0.90, 1.10), 2)))
            
            # Criar despesa
            d = Despesa(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=forn.id if forn else None,
                descricao=desp_data["descricao"],
                categoria=desp_data["categoria"],
                tipo="fixa",
                valor=valor,
                data_despesa=data_despesa,
                forma_pagamento="boleto",
                recorrente=True,
                observacoes=f"Ref. {mes:02d}/{ano} - Venc. {data_vencimento.isoformat()}",
            )
            db.session.add(d)
            despesas.append(d)
            
            # 🔥 GERAR ContaPagar (BOLETO) para esta despesa fixa
            # Status baseado na idade:
            # - Meses passados: 85% pago, 10% pago com atraso, 5% vencido (esquecido)
            # - Mês atual: 40% pago, 30% aberto, 20% vencido, 10% a vencer
            dias_ate_vencimento = (data_vencimento - hoje).days
            
            if mes_offset >= 2:
                # Meses antigos: maioria paga
                sorteio = random.random()
                if sorteio < 0.85:
                    status = "pago"
                    data_pgto = data_vencimento - timedelta(days=random.randint(0, 5))
                    valor_pago = valor
                    valor_atual = Decimal("0")
                elif sorteio < 0.95:
                    status = "pago"
                    data_pgto = data_vencimento + timedelta(days=random.randint(1, 15))
                    valor_pago = valor
                    valor_atual = Decimal("0")
                else:
                    status = "aberto"  # Boleto esquecido!
                    data_pgto = None
                    valor_pago = Decimal("0")
                    valor_atual = valor
                    boletos_vencidos += 1
            elif mes_offset == 1:
                # Mês passado: variado
                sorteio = random.random()
                if sorteio < 0.60:
                    status = "pago"
                    data_pgto = data_vencimento - timedelta(days=random.randint(0, 3))
                    valor_pago = valor
                    valor_atual = Decimal("0")
                elif sorteio < 0.80:
                    status = "aberto"  # Vencido e não pago
                    data_pgto = None
                    valor_pago = Decimal("0")
                    valor_atual = valor
                    boletos_vencidos += 1
                else:
                    status = "pago"
                    data_pgto = data_vencimento + timedelta(days=random.randint(1, 10))
                    valor_pago = valor
                    valor_atual = Decimal("0")
            else:
                # Mês atual
                if dias_ate_vencimento < 0:
                    # Venceu e não pagou
                    sorteio = random.random()
                    if sorteio < 0.50:
                        status = "pago"
                        data_pgto = data_vencimento + timedelta(days=random.randint(1, 5))
                        valor_pago = valor
                        valor_atual = Decimal("0")
                    else:
                        status = "aberto"
                        data_pgto = None
                        valor_pago = Decimal("0")
                        valor_atual = valor
                        boletos_vencidos += 1
                elif dias_ate_vencimento <= 7:
                    # Vence em breve
                    status = "aberto"
                    data_pgto = None
                    valor_pago = Decimal("0")
                    valor_atual = valor
                    boletos_abertos += 1
                else:
                    # Vence daqui a mais de 7 dias
                    status = "aberto"
                    data_pgto = None
                    valor_pago = Decimal("0")
                    valor_atual = valor
                    boletos_abertos += 1
            
            if status == "pago":
                boletos_pagos += 1
            
            boleto = ContaPagar(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=forn.id if forn else fornecedor_fallback.id,
                numero_documento=f"BOL-{desp_data['categoria'][:3].upper()}-{ano}{mes:02d}",
                tipo_documento="boleto",
                valor_original=valor,
                valor_pago=valor_pago,
                valor_atual=valor_atual,
                data_emissao=data_despesa,
                data_vencimento=data_vencimento,
                data_pagamento=data_pgto,
                status=status,
                forma_pagamento="boleto",
                observacoes=f"{desp_data['descricao']} - {mes:02d}/{ano}",
            )
            db.session.add(boleto)
            boletos_criados += 1
    
    # ═══════════════════════════════════════════════════════════
    # DESPESAS PROBLEMÁTICAS (para análise de corte)
    # ═══════════════════════════════════════════════════════════
    despesas_problematicas = [
        {"descricao": "Assinatura de revista de fofocas", "categoria": "Outros", "valor": 89.90, "recorrente": True},
        {"descricao": "Decoração de Natal fora de época", "categoria": "Marketing", "valor": 1200.00, "recorrente": False},
        {"descricao": "Almoço executivo em restaurante caro", "categoria": "Alimentação", "valor": 450.00, "recorrente": False},
        {"descricao": "Curso de astrologia empresarial", "categoria": "Treinamento", "valor": 890.00, "recorrente": False},
        {"descricao": "Plantas ornamentais de luxo", "categoria": "Outros", "valor": 650.00, "recorrente": False},
        {"descricao": "Assinatura de streaming premium", "categoria": "Outros", "valor": 55.90, "recorrente": True},
        {"descricao": "Consultoria de feng shui", "categoria": "Consultoria", "valor": 1500.00, "recorrente": False},
    ]
    
    for desp_data in despesas_problematicas:
        meses = range(3, -1, -1) if desp_data["recorrente"] else [random.randint(0, 2)]
        for mes_offset in meses:
            data_despesa = hoje - timedelta(days=30 * mes_offset)
            d = Despesa(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=None,
                descricao=desp_data["descricao"],
                categoria=desp_data["categoria"],
                tipo="variavel",
                valor=Decimal(str(desp_data["valor"])),
                data_despesa=data_despesa,
                forma_pagamento=random.choice(["cartao_credito", "pix"]),
                recorrente=desp_data["recorrente"],
                observacoes="Despesa questionável - revisar necessidade",
            )
            db.session.add(d)
            despesas.append(d)

    # ═══════════════════════════════════════════════════════════
    # DESPESAS VARIÁVEIS OPERACIONAIS
    # ═══════════════════════════════════════════════════════════
    despesas_variaveis = [
        ("Troca de lâmpadas LED", "Manutenção", 180.00),
        ("Resma de papel A4 (5un)", "Material de Escritório", 95.00),
        ("Sacolas plásticas biodegradáveis", "Embalagens", 320.00),
        ("Reparo na porta automática", "Manutenção", 450.00),
        ("Frete de mercadorias (complementar)", "Transporte", 280.00),
        ("Material de limpeza", "Limpeza", 150.00),
        ("Etiquetas e bobinas de impressão", "Material de Escritório", 120.00),
        ("Dedetização mensal", "Higiene", 200.00),
        ("Uniforme funcionários (3 kits)", "Pessoal", 360.00),
        ("Serviço de grafiteiro (fachada)", "Marketing", 800.00),
        ("Banner promocional", "Marketing", 150.00),
        ("Manutenção do refrigerador", "Manutenção", 550.00),
        ("Rolo filme PVC (10un)", "Embalagens", 85.00),
        ("Recarga extintor de incêndio", "Segurança", 120.00),
        ("Limpeza de caixa de gordura", "Manutenção", 250.00),
        ("Gasolina (entregas delivery)", "Transporte", 200.00),
        ("Luvas e toucas descartáveis", "Higiene", 90.00),
        ("Conserto do carrinho de compras", "Manutenção", 75.00),
        ("Pilhas e baterias", "Material de Escritório", 45.00),
        ("Reparo no piso cerâmico", "Manutenção", 380.00),
    ]
    
    for desc, cat, valor_base in despesas_variaveis:
        data_despesa = hoje - timedelta(days=random.randint(1, 180))
        forn = random.choice(fornecedores) if fornecedores and random.random() > 0.3 else None
        valor = Decimal(str(round(valor_base * random.uniform(0.85, 1.15), 2)))

        d = Despesa(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=forn.id if forn else None,
            descricao=desc,
            categoria=cat,
            tipo="variavel",
            valor=valor,
            data_despesa=data_despesa,
            forma_pagamento=random.choice(["pix", "dinheiro", "cartao_credito", "boleto"]),
            recorrente=False,
            observacoes=None,
        )
        db.session.add(d)
        despesas.append(d)
        
        # Se pagamento é boleto, gera ContaPagar
        if d.forma_pagamento == "boleto" and forn:
            data_venc = data_despesa + timedelta(days=random.randint(15, 45))
            pago = data_venc < hoje
            
            boleto = ContaPagar(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=forn.id,
                numero_documento=f"NF-{random.randint(10000, 99999)}",
                tipo_documento="nota_fiscal",
                valor_original=valor,
                valor_pago=valor if pago else Decimal("0"),
                valor_atual=Decimal("0") if pago else valor,
                data_emissao=data_despesa,
                data_vencimento=data_venc,
                data_pagamento=data_venc - timedelta(days=random.randint(0, 3)) if pago else None,
                status="pago" if pago else "aberto",
                forma_pagamento="boleto",
                observacoes=desc,
            )
            db.session.add(boleto)
            boletos_criados += 1
            if pago:
                boletos_pagos += 1
            elif data_venc < hoje:
                boletos_vencidos += 1
            else:
                boletos_abertos += 1

    db.session.commit()
    print(f"✅ {len(despesas)} despesas criadas (fixas + variáveis + problemáticas)")
    print(f"✅ {boletos_criados} boletos (ContaPagar) gerados:")
    print(f"   ✅ {boletos_pagos} pagos | 📋 {boletos_abertos} abertos | 🔴 {boletos_vencidos} vencidos")
    return despesas


def seed_contas_receber(
    estabelecimento_id: int,
    clientes: List[Cliente],
):
    """
    🔥 Gera contas a receber (vendas a prazo/fiado) para clientes.
    
    Cenários:
    - Vendas a prazo para clientes cadastrados
    - Parcelamentos (2x a 6x)
    - Status variado: recebido, aberto, vencido
    - Clientes bons pagadores vs inadimplentes
    """
    print("💰 Criando contas a receber (vendas a prazo)...")
    
    hoje = date.today()
    contas_criadas = 0
    contas_recebidas = 0
    contas_abertas = 0
    contas_vencidas = 0
    
    if not clientes:
        print("   ⚠️ Nenhum cliente para gerar contas a receber")
        return
    
    # ~30% dos clientes fazem compras a prazo
    clientes_prazo = random.sample(
        clientes,
        k=min(len(clientes), max(5, int(len(clientes) * 0.30)))
    )
    
    for cliente in clientes_prazo:
        # Cada cliente tem 1-4 compras a prazo ao longo dos últimos 90 dias
        num_compras = random.randint(1, 4)
        
        for _ in range(num_compras):
            data_compra = hoje - timedelta(days=random.randint(5, 90))
            valor_total = Decimal(str(round(random.uniform(50, 800), 2)))
            
            # Parcelamento: 1x a 4x
            num_parcelas = random.choice([1, 1, 2, 2, 3, 4])
            valor_parcela = (valor_total / num_parcelas).quantize(Decimal("0.01"))
            
            for parcela in range(1, num_parcelas + 1):
                data_venc = data_compra + timedelta(days=30 * parcela)
                dias_ate = (data_venc - hoje).days
                
                # Status baseado na data de vencimento
                if dias_ate < -30:
                    # Venceu há muito tempo
                    sorteio = random.random()
                    if sorteio < 0.75:
                        status = "recebido"
                        data_rec = data_venc + timedelta(days=random.randint(0, 15))
                    else:
                        status = "aberto"  # Inadimplente
                        data_rec = None
                        contas_vencidas += 1
                elif dias_ate < 0:
                    # Venceu recentemente
                    sorteio = random.random()
                    if sorteio < 0.50:
                        status = "recebido"
                        data_rec = data_venc + timedelta(days=random.randint(0, 5))
                    else:
                        status = "aberto"  # Vencido
                        data_rec = None
                        contas_vencidas += 1
                else:
                    # Ainda não venceu
                    status = "aberto"
                    data_rec = None
                    contas_abertas += 1
                
                if status == "recebido":
                    contas_recebidas += 1
                
                conta = ContaReceber(
                    estabelecimento_id=estabelecimento_id,
                    cliente_id=cliente.id,
                    numero_documento=f"CR-{data_compra.strftime('%Y%m%d')}-{random.randint(100, 999)}-{parcela}",
                    tipo_documento="duplicata" if num_parcelas > 1 else "recibo",
                    valor_original=valor_parcela,
                    valor_recebido=valor_parcela if status == "recebido" else Decimal("0"),
                    valor_atual=Decimal("0") if status == "recebido" else valor_parcela,
                    data_emissao=data_compra,
                    data_vencimento=data_venc,
                    data_recebimento=data_rec,
                    status=status,
                    forma_recebimento="pix" if status == "recebido" else None,
                    observacoes=f"Parcela {parcela}/{num_parcelas}" if num_parcelas > 1 else "Pagamento à vista (prazo)",
                )
                db.session.add(conta)
                contas_criadas += 1
    
    db.session.commit()
    print(f"✅ {contas_criadas} contas a receber criadas para {len(clientes_prazo)} clientes")
    print(f"   ✅ {contas_recebidas} recebidas | 📋 {contas_abertas} abertas | 🔴 {contas_vencidas} vencidas")


def seed_ponto(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    dias_passados: int = 90,
):
    """
    Cria histórico COMPLETO e realista de registros de ponto.
    
    Cenários por funcionário:
    - Dias normais (pontual, 4 registros)
    - Dias com atraso na entrada
    - Dias com hora extra (saída após 18h)
    - Dias com atraso no retorno do almoço
    - Dias de falta (sem registros)
    - Dias com apenas entrada (esqueceu de bater saída)
    
    Cada funcionário tem um "perfil" comportamental:
    - Pontual: raramente atrasa, nunca faz hora extra
    - Normal: atrasa às vezes, hora extra ocasional
    - Atrasado crônico: atrasa frequentemente
    - Trabalhador: faz muita hora extra
    """
    print(f"⏰ Criando histórico de ponto ({dias_passados} dias)...")
    
    # Criar configuração de horários
    config = ConfiguracaoHorario.query.filter_by(
        estabelecimento_id=estabelecimento_id
    ).first()
    
    if not config:
        config = ConfiguracaoHorario(
            estabelecimento_id=estabelecimento_id,
            hora_entrada=time(8, 0),
            hora_saida_almoco=time(12, 0),
            hora_retorno_almoco=time(13, 0),
            hora_saida=time(18, 0),
            tolerancia_entrada=10,
            tolerancia_saida_almoco=5,
            tolerancia_retorno_almoco=10,
            tolerancia_saida=5,
            exigir_foto=True,
            exigir_localizacao=False,
            raio_permitido_metros=100,
        )
        db.session.add(config)
        db.session.flush()
    
    funcionarios_filtrados = [f for f in funcionarios if f.ativo and f.role in ("ADMIN", "FUNCIONARIO")]
    if not funcionarios_filtrados:
        print("   ⚠️ Nenhum funcionário ativo para criar ponto")
        return 0
    
    # Perfis comportamentais para cada funcionário
    perfis = ["pontual", "normal", "atrasado_cronico", "trabalhador"]
    perfil_funcionario = {}
    for func in funcionarios_filtrados:
        if func.cargo in ("Gerente", "Administrador"):
            perfil_funcionario[func.id] = "trabalhador"  # Gerentes fazem mais HE
        elif func.cargo == "Operador de Caixa":
            perfil_funcionario[func.id] = random.choice(["pontual", "normal"])
        else:
            perfil_funcionario[func.id] = random.choice(perfis)
    
    pontos_criados = 0
    dias_atraso = 0
    dias_hora_extra = 0
    dias_falta = 0
    hoje = date.today()
    
    for dias_atras in range(dias_passados, 0, -1):
        data_registro = hoje - timedelta(days=dias_atras)
        
        # Pular fins de semana
        if data_registro.weekday() >= 5:
            continue
        
        for funcionario in funcionarios_filtrados:
            perfil = perfil_funcionario.get(funcionario.id, "normal")
            
            # ═══ CENÁRIO: FALTA ═══
            # Probabilidade de falta baseada no perfil
            prob_falta = {
                "pontual": 0.02,       # 2% - quase nunca falta
                "normal": 0.05,        # 5% - falta ocasional
                "atrasado_cronico": 0.10,  # 10% - falta mais
                "trabalhador": 0.03,   # 3% - raramente falta
            }
            if random.random() < prob_falta.get(perfil, 0.05):
                dias_falta += 1
                continue  # Sem registros neste dia
            
            # ═══ ENTRADA ═══
            variacao_entrada = {
                "pontual": random.randint(-10, 5),      # Quase sempre no horário
                "normal": random.randint(-5, 15),        # Variação moderada
                "atrasado_cronico": random.randint(5, 40),  # Frequentemente atrasado
                "trabalhador": random.randint(-15, 5),   # Chega cedo
            }
            min_entrada = variacao_entrada.get(perfil, random.randint(-5, 15))
            hora_ent = (datetime.combine(data_registro, time(8, 0)) + timedelta(minutes=min_entrada)).time()
            
            atraso_entrada = max(0, min_entrada - 10)  # Tolerância de 10min
            status_ent = "atrasado" if atraso_entrada > 0 else "normal"
            if atraso_entrada > 0:
                dias_atraso += 1
            
            entrada = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_ent,
                tipo_registro="entrada",
                status=status_ent,
                minutos_atraso=atraso_entrada,
                dispositivo="Chrome/Windows" if random.random() > 0.3 else "Safari/iOS",
                ip_address=f"192.168.1.{random.randint(10, 254)}",
                observacao="Entrada matinal" if status_ent == "normal" else f"Atraso de {atraso_entrada}min",
            )
            db.session.add(entrada)
            pontos_criados += 1
            
            # ═══ CENÁRIO: ESQUECEU DE BATER SAÍDA (raro) ═══
            if random.random() < 0.03:  # 3% das vezes
                continue  # Só bateu entrada
            
            # ═══ SAÍDA ALMOÇO ═══
            min_saida_alm = random.randint(-5, 10)
            hora_sa = (datetime.combine(data_registro, time(12, 0)) + timedelta(minutes=min_saida_alm)).time()
            
            saida_almoco = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_sa,
                tipo_registro="saida_almoco",
                status="normal",
                minutos_atraso=0,
                observacao="Saída para almoço",
            )
            db.session.add(saida_almoco)
            pontos_criados += 1
            
            # ═══ RETORNO ALMOÇO ═══
            variacao_retorno = {
                "pontual": random.randint(-5, 5),
                "normal": random.randint(-3, 15),
                "atrasado_cronico": random.randint(5, 25),
                "trabalhador": random.randint(-10, 5),
            }
            min_retorno = variacao_retorno.get(perfil, random.randint(-5, 15))
            hora_ret = (datetime.combine(data_registro, time(13, 0)) + timedelta(minutes=min_retorno)).time()
            atraso_retorno = max(0, min_retorno - 10)
            
            retorno_almoco = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_ret,
                tipo_registro="retorno_almoco",
                status="atrasado" if atraso_retorno > 0 else "normal",
                minutos_atraso=atraso_retorno,
                observacao="Retorno do almoço",
            )
            db.session.add(retorno_almoco)
            pontos_criados += 1
            
            # ═══ SAÍDA ═══
            variacao_saida = {
                "pontual": random.randint(-5, 5),       # Sai no horário
                "normal": random.randint(-5, 30),        # Às vezes faz HE
                "atrasado_cronico": random.randint(-10, 10),  # Sai no horário
                "trabalhador": random.randint(15, 120),  # Faz MUITA hora extra
            }
            min_saida = variacao_saida.get(perfil, random.randint(-5, 30))
            hora_sai = (datetime.combine(data_registro, time(18, 0)) + timedelta(minutes=min_saida)).time()
            
            is_hora_extra = min_saida > 5  # Saiu mais de 5min depois
            if is_hora_extra:
                dias_hora_extra += 1
            
            saida = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_sai,
                tipo_registro="saida",
                status="normal",
                minutos_atraso=0,
                observacao=f"Hora extra: +{min_saida}min" if is_hora_extra else "Saída normal",
            )
            db.session.add(saida)
            pontos_criados += 1

            # 🔥 Commit em lotes para evitar timeout no Neon
            if pontos_criados % 100 == 0:
                db.session.commit()
    
    db.session.commit()
    print(f"✅ {pontos_criados} registros de ponto criados ({dias_passados} dias)")
    print(f"   📊 {dias_atraso} dias com atraso | {dias_hora_extra} dias com hora extra | {dias_falta} faltas")
    
    # Resumo de perfis
    for perfil_nome in set(perfil_funcionario.values()):
        qtd = sum(1 for p in perfil_funcionario.values() if p == perfil_nome)
        print(f"   👤 {qtd} funcionário(s) com perfil '{perfil_nome}'")
    
    return pontos_criados


def seed_beneficios(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
):
    """
    Cria benefícios do estabelecimento e atribui a funcionários.
    
    Benefícios típicos de supermercado:
    - Vale Transporte, Vale Alimentação, Plano de Saúde, etc.
    - Cada funcionário recebe 2-5 benefícios com valores variados
    """
    print("🎁 Criando benefícios e atribuindo a funcionários...")
    
    beneficios_data = [
        {"nome": "Vale Transporte", "descricao": "Auxílio transporte público municipal", "valor_padrao": 220.00},
        {"nome": "Vale Alimentação", "descricao": "Cartão alimentação mensal", "valor_padrao": 450.00},
        {"nome": "Vale Refeição", "descricao": "Refeição diária no trabalho", "valor_padrao": 25.00},
        {"nome": "Plano de Saúde", "descricao": "Plano de saúde coletivo empresarial", "valor_padrao": 350.00},
        {"nome": "Plano Odontológico", "descricao": "Assistência odontológica", "valor_padrao": 80.00},
        {"nome": "Seguro de Vida", "descricao": "Seguro de vida em grupo", "valor_padrao": 30.00},
        {"nome": "Cesta Básica", "descricao": "Cesta básica mensal do estabelecimento", "valor_padrao": 180.00},
        {"nome": "Auxílio Creche", "descricao": "Auxílio para funcionários com filhos até 5 anos", "valor_padrao": 300.00},
        {"nome": "Participação nos Lucros", "descricao": "PLR semestral baseado em metas", "valor_padrao": 500.00},
        {"nome": "Desconto em Produtos", "descricao": "10% de desconto nas compras do estabelecimento", "valor_padrao": 0.00},
    ]
    
    beneficios = []
    for ben_data in beneficios_data:
        ben = Beneficio(
            estabelecimento_id=estabelecimento_id,
            nome=ben_data["nome"],
            descricao=ben_data["descricao"],
            valor_padrao=Decimal(str(ben_data["valor_padrao"])),
            ativo=True,
        )
        db.session.add(ben)
        beneficios.append(ben)
    
    db.session.flush()
    
    # Atribuir benefícios aos funcionários ativos
    funcionarios_ativos = [f for f in funcionarios if f.ativo]
    atribuicoes = 0
    
    for func in funcionarios_ativos:
        # Todos recebem VT, VA e Seguro de Vida (obrigatórios)
        beneficios_obrigatorios = [b for b in beneficios if b.nome in (
            "Vale Transporte", "Vale Alimentação", "Seguro de Vida"
        )]
        
        # Selecionar 1-3 benefícios opcionais adicionais
        beneficios_opcionais = [b for b in beneficios if b not in beneficios_obrigatorios]
        num_opcionais = random.randint(1, min(3, len(beneficios_opcionais)))
        beneficios_selecionados = beneficios_obrigatorios + random.sample(beneficios_opcionais, num_opcionais)
        
        # Gerentes/Admin recebem mais benefícios
        if func.cargo in ("Gerente", "Administrador"):
            extras = [b for b in beneficios_opcionais if b not in beneficios_selecionados]
            beneficios_selecionados += random.sample(extras, min(2, len(extras)))
        
        for ben in beneficios_selecionados:
            # Valor pode variar ±20% do padrão baseado no cargo
            valor_base = float(ben.valor_padrao)
            if valor_base > 0:
                fator_cargo = 1.0
                if func.cargo in ("Gerente", "Administrador"):
                    fator_cargo = random.uniform(1.1, 1.3)  # +10-30%
                elif func.cargo == "Supervisor":
                    fator_cargo = random.uniform(1.0, 1.15)
                valor_func = round(valor_base * fator_cargo, 2)
            else:
                valor_func = 0.0
            
            fb = FuncionarioBeneficio(
                funcionario_id=func.id,
                beneficio_id=ben.id,
                valor=Decimal(str(valor_func)),
                data_inicio=func.data_admissao,
                ativo=True,
            )
            db.session.add(fb)
            atribuicoes += 1
    
    db.session.commit()
    print(f"✅ {len(beneficios)} benefícios criados | {atribuicoes} atribuições a {len(funcionarios_ativos)} funcionários")


def seed_banco_horas(
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    meses_passados: int = 3,
):
    """
    Calcula e registra o banco de horas baseado nos registros de ponto existentes.
    
    Para cada funcionário e cada mês:
    - Soma horas trabalhadas (entrada→saída com desconto de almoço)
    - Compara com horas esperadas (8h × dias úteis do mês)
    - Saldo positivo = hora extra, negativo = devedor
    - Calcula valor monetário da hora extra (50% sobre hora normal)
    """
    print("⏱️ Calculando banco de horas baseado nos registros de ponto...")
    
    hoje = date.today()
    registros_criados = 0
    
    funcionarios_ativos = [f for f in funcionarios if f.ativo and f.role in ("ADMIN", "FUNCIONARIO")]
    
    for func in funcionarios_ativos:
        salario_hora = float(func.salario_base or 1800) / 220  # 220h mensais (CLT)
        valor_he_50 = salario_hora * 1.5  # 50% adicional
        
        for mes_offset in range(meses_passados, -1, -1):
            # Calcular mês de referência
            ano = hoje.year
            mes = hoje.month - mes_offset
            while mes <= 0:
                mes += 12
                ano -= 1
            mes_ref = f"{ano:04d}-{mes:02d}"
            
            # Buscar registros de ponto deste mês
            primeiro_dia = date(ano, mes, 1)
            if mes == 12:
                ultimo_dia = date(ano + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo_dia = date(ano, mes + 1, 1) - timedelta(days=1)
            
            # Limitar ao hoje se for mês atual
            if ultimo_dia > hoje:
                ultimo_dia = hoje
            
            registros = RegistroPonto.query.filter(
                RegistroPonto.funcionario_id == func.id,
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data.between(primeiro_dia, ultimo_dia),
            ).order_by(RegistroPonto.data, RegistroPonto.hora).all()
            
            # Agrupar registros por dia
            registros_por_dia = {}
            for reg in registros:
                if reg.data not in registros_por_dia:
                    registros_por_dia[reg.data] = {}
                registros_por_dia[reg.data][reg.tipo_registro] = reg
            
            # Calcular horas trabalhadas
            total_minutos_trabalhados = 0
            dias_trabalhados = 0
            
            for data_dia, regs_dia in registros_por_dia.items():
                entrada = regs_dia.get("entrada")
                saida = regs_dia.get("saida")
                saida_alm = regs_dia.get("saida_almoco")
                retorno_alm = regs_dia.get("retorno_almoco")
                
                if entrada and saida:
                    # Período manhã + tarde
                    dt_entrada = datetime.combine(data_dia, entrada.hora)
                    dt_saida = datetime.combine(data_dia, saida.hora)
                    
                    # Desconto almoço
                    minutos_almoco = 60  # Padrão 1h
                    if saida_alm and retorno_alm:
                        dt_sa = datetime.combine(data_dia, saida_alm.hora)
                        dt_ret = datetime.combine(data_dia, retorno_alm.hora)
                        minutos_almoco = max(0, int((dt_ret - dt_sa).total_seconds() / 60))
                    
                    minutos_dia = max(0, int((dt_saida - dt_entrada).total_seconds() / 60) - minutos_almoco)
                    total_minutos_trabalhados += minutos_dia
                    dias_trabalhados += 1
            
            # Calcular dias úteis esperados no mês
            dias_uteis = 0
            d = primeiro_dia
            while d <= ultimo_dia:
                if d.weekday() < 5:  # Segunda a sexta
                    dias_uteis += 1
                d += timedelta(days=1)
            
            horas_esperadas_minutos = dias_uteis * 480  # 8h × 60min
            saldo_minutos = total_minutos_trabalhados - horas_esperadas_minutos
            
            # Calcular valor das horas extras (apenas saldo positivo)
            horas_extras = max(0, saldo_minutos) / 60.0
            valor_he = round(horas_extras * valor_he_50, 2)
            
            banco = BancoHoras(
                funcionario_id=func.id,
                mes_referencia=mes_ref,
                saldo_minutos=saldo_minutos,
                valor_hora_extra=Decimal(str(valor_he)),
                horas_trabalhadas_minutos=total_minutos_trabalhados,
                horas_esperadas_minutos=horas_esperadas_minutos,
            )
            db.session.add(banco)
            registros_criados += 1
    
    db.session.commit()
    
    # Estatísticas
    total_he_positivo = db.session.query(db.func.count(BancoHoras.id)).filter(
        BancoHoras.saldo_minutos > 0
    ).scalar()
    total_he_negativo = db.session.query(db.func.count(BancoHoras.id)).filter(
        BancoHoras.saldo_minutos < 0
    ).scalar()
    
    print(f"✅ {registros_criados} registros de banco de horas criados")
    print(f"   📈 {total_he_positivo} meses com hora extra (saldo positivo)")
    print(f"   📉 {total_he_negativo} meses com saldo negativo (devedor)")


def seed_justificativas(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    dias_passados: int = 90,
):
    """
    Cria justificativas de ponto realistas baseadas nos registros existentes.
    
    Cenários:
    - Justificativas de atraso (com e sem atestado)
    - Justificativas de falta (atestado médico, compromisso pessoal)
    - Justificativas de saída antecipada
    - Justificativas de hora extra
    - Status variados: pendente, aprovado, rejeitado
    """
    print("📋 Criando justificativas de ponto...")
    
    hoje = date.today()
    justificativas_criadas = 0
    
    funcionarios_ativos = [f for f in funcionarios if f.ativo and f.role in ("ADMIN", "FUNCIONARIO")]
    if not funcionarios_ativos:
        print("   ⚠️ Nenhum funcionário ativo")
        return
    
    # Funcionários que podem aprovar
    aprovadores = [f for f in funcionarios if f.cargo in ("Gerente", "Administrador")]
    if not aprovadores:
        aprovadores = funcionarios_ativos[:1]
    
    motivos_atraso = [
        "Trânsito congestionado na BR-101",
        "Problema mecânico no carro",
        "Ônibus atrasou na linha 42",
        "Consulta médica de emergência",
        "Acompanhamento de filho ao médico",
        "Acidente na via de acesso",
        "Problema com transporte público",
        "Chuva forte na região",
        "Enchente na rua de casa",
    ]
    
    motivos_falta = [
        "Atestado médico - gripe",
        "Atestado médico - consulta oftalmologista",
        "Atestado médico - exame de sangue",
        "Acompanhamento de familiar ao hospital",
        "Falecimento de parente",
        "Audiência judicial",
        "Compromisso no cartório",
        "Problema familiar urgente",
        "Doação de sangue",
        "Atestado médico - procedimento odontológico",
    ]
    
    motivos_saida_antecipada = [
        "Consulta médica agendada",
        "Reunião escolar do filho",
        "Problema de saúde familiar",
        "Compromisso no banco (horário comercial)",
        "Emergência domiciliar",
    ]
    
    motivos_hora_extra = [
        "Fechamento de balanço mensal",
        "Inventário de estoque",
        "Promoção especial - alto movimento",
        "Cobertura de colega ausente",
        "Reposição de mercadorias urgente",
        "Preparação para auditoria",
        "Período de alta demanda (feriado próximo)",
    ]
    
    for func in funcionarios_ativos:
        # Cada funcionário tem 3-8 justificativas ao longo do período
        num_justificativas = random.randint(3, 8)
        
        for _ in range(num_justificativas):
            data_just = hoje - timedelta(days=random.randint(1, dias_passados))
            
            # Tipo da justificativa
            tipo = random.choices(
                ["atraso", "falta", "saida_antecipada", "hora_extra"],
                weights=[40, 25, 15, 20],
                k=1,
            )[0]
            
            if tipo == "atraso":
                motivo = random.choice(motivos_atraso)
            elif tipo == "falta":
                motivo = random.choice(motivos_falta)
            elif tipo == "saida_antecipada":
                motivo = random.choice(motivos_saida_antecipada)
            else:
                motivo = random.choice(motivos_hora_extra)
            
            # Status: mais velhas tendem a estar resolvidas
            dias_atras = (hoje - data_just).days
            if dias_atras > 30:
                status = random.choices(
                    ["aprovado", "rejeitado"],
                    weights=[80, 20],
                    k=1,
                )[0]
            elif dias_atras > 7:
                status = random.choices(
                    ["aprovado", "rejeitado", "pendente"],
                    weights=[60, 15, 25],
                    k=1,
                )[0]
            else:
                status = random.choices(
                    ["pendente", "aprovado"],
                    weights=[70, 30],
                    k=1,
                )[0]
            
            aprovador = random.choice(aprovadores) if status != "pendente" else None
            data_resposta = None
            motivo_rejeicao = None
            
            if status != "pendente":
                data_resposta = datetime.combine(
                    data_just + timedelta(days=random.randint(1, 5)),
                    time(random.randint(9, 17), random.randint(0, 59)),
                )
            
            if status == "rejeitado":
                motivo_rejeicao = random.choice([
                    "Sem comprovante anexado",
                    "Justificativa insuficiente",
                    "Recorrência excessiva",
                    "Fora do prazo de envio",
                    "Não se enquadra na política interna",
                ])
            
            # Documento (30% das justificativas tem documento)
            doc_url = None
            if random.random() < 0.30 and tipo in ("falta", "atraso"):
                doc_url = f"/uploads/justificativas/atestado_{func.id}_{data_just.isoformat()}.pdf"
            
            just = JustificativaPonto(
                estabelecimento_id=estabelecimento_id,
                funcionario_id=func.id,
                aprovador_id=aprovador.id if aprovador else None,
                tipo=tipo,
                data=data_just,
                motivo=motivo,
                documento_url=doc_url,
                status=status,
                data_resposta=data_resposta,
                motivo_rejeicao=motivo_rejeicao,
                created_at=datetime.combine(data_just, time(random.randint(8, 18), random.randint(0, 59))),
            )
            db.session.add(just)
            justificativas_criadas += 1
    
    db.session.commit()
    
    # Estatísticas
    pendentes = sum(1 for _ in db.session.query(JustificativaPonto).filter_by(
        estabelecimento_id=estabelecimento_id, status="pendente"
    ))
    aprovadas = sum(1 for _ in db.session.query(JustificativaPonto).filter_by(
        estabelecimento_id=estabelecimento_id, status="aprovado"
    ))
    rejeitadas = sum(1 for _ in db.session.query(JustificativaPonto).filter_by(
        estabelecimento_id=estabelecimento_id, status="rejeitado"
    ))
    
    print(f"✅ {justificativas_criadas} justificativas criadas")
    print(f"   ⏳ {pendentes} pendentes | ✅ {aprovadas} aprovadas | ❌ {rejeitadas} rejeitadas")


def seed_caixas(fake: Faker, estabelecimento_id: int, funcionarios: List[Funcionario]):
    """Cria caixas e movimentações."""
    print("💰 Criando caixas...")

    hoje = datetime.now()
    caixas = []

    # Criar caixas dos últimos 7 dias
    for dia_offset in range(7, -1, -1):
        data_abertura = hoje - timedelta(days=dia_offset, hours=random.randint(0, 23))
        funcionario = random.choice(
            [f for f in funcionarios if "Caixa" in f.cargo or "ADMIN" in f.role]
        )

        saldo_inicial = Decimal(str(round(random.uniform(200, 500), 2)))

        caixa = Caixa(
            estabelecimento_id=estabelecimento_id,
            funcionario_id=funcionario.id,
            numero_caixa=f"C{random.randint(1, 3)}",
            saldo_inicial=saldo_inicial,
            saldo_final=(
                None
                if dia_offset == 0
                else saldo_inicial + Decimal(str(round(random.uniform(1000, 5000), 2)))
            ),
            saldo_atual=saldo_inicial,
            data_abertura=data_abertura,
            data_fechamento=(
                data_abertura + timedelta(hours=8) if dia_offset > 0 else None
            ),
            status="aberto" if dia_offset == 0 else "fechado",
            observacoes=None,
        )

        db.session.add(caixa)
        caixas.append(caixa)

    db.session.flush()
    print(f"✅ {len(caixas)} caixas criados")
    return caixas


def seed_dashboard_metricas(estabelecimento_id: int):
    """Cria métricas do dashboard."""
    print("📊 Criando métricas do dashboard...")

    hoje = date.today()

    for dia_offset in range(30, -1, -1):
        data_ref = hoje - timedelta(days=dia_offset)

        metrica = DashboardMetrica(
            estabelecimento_id=estabelecimento_id,
            data_referencia=data_ref,
            total_vendas_dia=Decimal(str(round(random.uniform(1000, 5000), 2))),
            quantidade_vendas_dia=random.randint(20, 80),
            ticket_medio_dia=Decimal(str(round(random.uniform(50, 150), 2))),
            clientes_atendidos_dia=random.randint(15, 60),
            total_vendas_mes=Decimal(str(round(random.uniform(30000, 80000), 2))),
            total_despesas_mes=Decimal(str(round(random.uniform(15000, 30000), 2))),
            lucro_bruto_mes=Decimal(str(round(random.uniform(5000, 15000), 2))),
            crescimento_vs_ontem=Decimal(str(round(random.uniform(-10, 20), 2))),
            crescimento_mensal=Decimal(str(round(random.uniform(-5, 25), 2))),
            tendencia_vendas=random.choice(["alta", "estavel", "baixa"]),
            top_produtos_json=json.dumps(
                [
                    {
                        "nome": "Coca-Cola 2L",
                        "quantidade": random.randint(20, 50),
                        "valor": round(random.uniform(200, 500), 2),
                    },
                    {
                        "nome": "Arroz 5kg",
                        "quantidade": random.randint(15, 30),
                        "valor": round(random.uniform(300, 600), 2),
                    },
                    {
                        "nome": "Sabonete",
                        "quantidade": random.randint(10, 25),
                        "valor": round(random.uniform(50, 150), 2),
                    },
                ]
            ),
            produtos_abc_json=json.dumps(
                {
                    "A": ["Coca-Cola 2L", "Arroz 5kg", "Feijão 1kg"],
                    "B": ["Macarrão", "Óleo", "Açúcar"],
                    "C": ["Temperos", "Molhos", "Conservas"],
                }
            ),
            segmentacao_clientes_json=json.dumps(
                {
                    "frequentes": random.randint(5, 15),
                    "esporadicos": random.randint(20, 40),
                    "novos": random.randint(1, 5),
                }
            ),
            alertas_json=json.dumps(
                [
                    {
                        "tipo": "estoque",
                        "mensagem": "Arroz Tio João abaixo do mínimo",
                        "criticidade": "alta",
                    },
                    {
                        "tipo": "validade",
                        "mensagem": "Leite vence em 3 dias",
                        "criticidade": "media",
                    },
                ]
            ),
            insights_json=json.dumps(
                [
                    {
                        "titulo": "Aumento nas vendas de bebidas",
                        "descricao": "Vendas aumentaram 15% nesta semana",
                    },
                    {
                        "titulo": "Cliente frequente",
                        "descricao": "Maria Silva fez 5 compras este mês",
                    },
                ]
            ),
        )

        db.session.add(metrica)

    db.session.commit()
    print("✅ Métricas do dashboard criadas")


def seed_relatorios_agendados(fake: Faker, estabelecimento_id: int):
    """Cria relatórios agendados."""
    print("📄 Criando relatórios agendados...")

    relatorios = [
        {
            "nome": "Relatório Diário de Vendas",
            "tipo": "vendas_diarias",
            "formato": "PDF",
            "frequencia": "diario",
            "horario_envio": time(18, 0),
            "destinatarios": ["gerente@empresa.com", "dono@empresa.com"],
            "enviar_para_proprietario": True,
        },
        {
            "nome": "Relatório Mensal Financeiro",
            "tipo": "financeiro_mensal",
            "formato": "EXCEL",
            "frequencia": "mensal",
            "horario_envio": time(9, 0),
            "destinatarios": ["contabilidade@empresa.com"],
            "enviar_para_proprietario": True,
        },
        {
            "nome": "Relatório de Estoque",
            "tipo": "estoque",
            "formato": "PDF",
            "frequencia": "semanal",
            "horario_envio": time(8, 30),
            "destinatarios": ["estoque@empresa.com"],
            "enviar_para_proprietario": False,
        },
    ]

    for rel_data in relatorios:
        r = RelatorioAgendado(
            estabelecimento_id=estabelecimento_id,
            nome=rel_data["nome"],
            tipo=rel_data["tipo"],
            formato=rel_data["formato"],
            frequencia=rel_data["frequencia"],
            horario_envio=rel_data["horario_envio"],
            destinatarios_email_json=json.dumps(rel_data["destinatarios"]),
            enviar_para_proprietario=rel_data["enviar_para_proprietario"],
            parametros_json=json.dumps({"dias": 30, "detalhado": True}),
            ativo=True,
            ultima_execucao=datetime.now() - timedelta(days=random.randint(1, 7)),
            proxima_execucao=datetime.now() + timedelta(days=1),
        )

        db.session.add(r)

    db.session.commit()
    print("✅ Relatórios agendados criados")


def seed_login_history(
    fake: Faker, estabelecimento_id: int, funcionarios: List[Funcionario]
):
    """Cria histórico de login."""
    print("🔐 Criando histórico de login...")

    for _ in range(50):
        funcionario = random.choice(funcionarios)
        data_login = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        lh = LoginHistory(
            funcionario_id=funcionario.id,
            username=funcionario.username,
            estabelecimento_id=estabelecimento_id,
            ip_address=fake.ipv4(),
            dispositivo=random.choice(["Windows 10", "Android", "iOS", "Linux"]),
            user_agent=fake.user_agent(),
            success=random.random() > 0.1,  # 90% de sucesso
            observacoes="Bloqueado temporariamente" if random.random() > 0.9 else None,
            created_at=data_login,
        )

        db.session.add(lh)

    db.session.commit()
    print("✅ Histórico de login criado")


# 🔥 NOVA FUNÇÃO: Teste de login do admin
def test_admin_login():
    """Testa se o admin pode logar com a senha admin123."""
    print("\n" + "=" * 60)
    print("🔐 TESTE DE LOGIN DO ADMIN")
    print("=" * 60)

    admin = Funcionario.query.filter_by(username="admin").first()
    if not admin:
        print("❌ ERRO: Admin não encontrado no banco!")
        return False

    print(f"Admin encontrado: {admin.nome}")
    print(f"Username: {admin.username}")
    print(f"Role: {admin.role}")
    print(f"Ativo: {admin.ativo}")

    # Testar senha
    if hasattr(admin, "check_senha"):
        if admin.check_senha("admin123"):
            print("✅ SUCESSO: Admin pode logar com 'admin123'!")
            return True
        else:
            print("❌ FALHA: Senha 'admin123' NÃO FUNCIONA!")
            print(
                f"   Hash armazenado: {admin.senha_hash[:50]}..."
                if admin.senha_hash
                else "Nenhum hash"
            )
            
            # Tentar corrigir a senha
            print("\n🔧 Tentando corrigir a senha...")
            admin.set_senha("admin123")
            db.session.commit()
            db.session.refresh(admin)
            
            if admin.check_senha("admin123"):
                print("✅ Senha corrigida com sucesso!")
                return True
            else:
                print("❌ Ainda não funciona após correção!")
                return False
    else:
        print("⚠️  AVISO: Método check_senha não encontrado no model")
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """Função principal do seed."""
    parser = argparse.ArgumentParser(
        description="Seed de dados completo para ERP Comercial"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Apaga e recria todos os dados"
    )
    parser.add_argument(
        "--estabelecimento-id", type=int, default=DEFAULT_ESTABELECIMENTO_ID
    )
    parser.add_argument("--clientes", type=int, default=100)  # 100 clientes
    parser.add_argument("--fornecedores", type=int, default=50)  # 50 fornecedores
    parser.add_argument("--produtos", type=int, default=200)  # 200 produtos
    parser.add_argument("--dias", type=int, default=300)  # 300 dias de histórico
    parser.add_argument("--test-login", action="store_true", help="Apenas testa login")
    parser.add_argument("--local", action="store_true", help="Popula APENAS banco local (SQLite)")
    parser.add_argument("--cloud", action="store_true", help="Popula APENAS banco na nuvem (Neon/Postgres)")
    parser.add_argument("--both", action="store_true", help="Popula AMBOS: local (SQLite) + nuvem (Neon/Postgres)")

    args = parser.parse_args(argv)

    # 🔥 --both: Executa o seed nos dois bancos sequencialmente
    if args.both:
        import subprocess
        print("=" * 60)
        print("🔄 MODO BOTH: Semeando LOCAL + NUVEM")
        print("=" * 60)
        
        base_args = []
        if args.reset:
            base_args.append("--reset")
        base_args += [
            "--clientes", str(args.clientes),
            "--fornecedores", str(args.fornecedores),
            "--produtos", str(args.produtos),
            "--dias", str(args.dias),
        ]
        
        # 1. Semear LOCAL
        print("\n" + "=" * 60)
        print("📦 [1/2] SEMEANDO BANCO LOCAL (SQLite)")
        print("=" * 60)
        result_local = subprocess.run(
            [sys.executable, __file__, "--local"] + base_args,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        
        # 2. Semear NUVEM
        print("\n" + "=" * 60)
        print("☁️ [2/2] SEMEANDO BANCO NUVEM (Neon/Postgres)")
        print("=" * 60)
        result_cloud = subprocess.run(
            [sys.executable, __file__, "--cloud"] + base_args,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        
        if result_local.returncode == 0 and result_cloud.returncode == 0:
            print("\n✅ AMBOS OS BANCOS SEMEADOS COM SUCESSO!")
        else:
            if result_local.returncode != 0:
                print("\n❌ FALHA no seed LOCAL")
            if result_cloud.returncode != 0:
                print("\n❌ FALHA no seed NUVEM")
        
        return max(result_local.returncode, result_cloud.returncode)

    fake = _faker()

    if args.local:
        # Remover variáveis de ambiente que apontam para bancos externos
        for key in ["AIVEN_DATABASE_URL", "NEON_DATABASE_URL", "DATABASE_URL_TARGET", "DB_PRIMARY", "DATABASE_URL", "POSTGRES_URL"]:
            if key in os.environ:
                del os.environ[key]
        print("🏠 Modo LOCAL: Populando APENAS SQLite")

    elif args.cloud:
        # Buscar URL do banco cloud (Aiven, Neon ou genérico)
        cloud_url = (
            os.environ.get("AIVEN_DATABASE_URL")
            or os.environ.get("NEON_DATABASE_URL")
            or os.environ.get("DATABASE_URL")
        )
        if not cloud_url:
            # Tentar ler do .env
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        for prefix in ["AIVEN_DATABASE_URL=", "NEON_DATABASE_URL=", "DATABASE_URL="]:
                            if line.startswith(prefix):
                                cloud_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                                break
                        if cloud_url:
                            break

        if not cloud_url:
            print("❌ URL do banco cloud não definida!")
            print("   Configure no .env: AIVEN_DATABASE_URL=postgres://user:pass@host:port/db?sslmode=require")
            return 1

        # Normalizar protocolo
        if cloud_url.startswith("postgres://"):
            cloud_url = cloud_url.replace("postgres://", "postgresql://", 1)

        # Injetar como DATABASE_URL para que create_app() use o banco cloud
        os.environ["DATABASE_URL"] = cloud_url

        print(f"☁️ Modo CLOUD: Populando PostgreSQL")
        if "@" in cloud_url:
            host_part = cloud_url.split("@")[1].split("/")[0]
            print(f"   Host: {host_part}")

    app = create_app(os.getenv("FLASK_ENV", "default"))

    with app.app_context():
        # Pré-teste de conectividade (evita falhar no meio do seed)
        if args.cloud or args.both:
            try:
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                print("✅ Conexão com banco cloud verificada")
            except Exception as conn_err:
                err_str = str(conn_err).lower()
                if "translate host" in err_str or "name or service not known" in err_str or "could not connect" in err_str or "connection refused" in err_str:
                    host = "?"
                    try:
                        url = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
                        if "@" in url:
                            host = url.split("@")[1].split("/")[0]
                    except Exception:
                        pass
                    print(f"\n❌ ERRO: Não foi possível conectar ao banco PostgreSQL.")
                    print(f"   Host usado: {host}")
                    print("\n   Verifique:")
                    print("   1. AIVEN_DATABASE_URL no .env com a URL correta do seu provedor (Aiven, Neon, etc).")
                    print("   2. O serviço PostgreSQL está ativo no painel do provedor.")
                    print("   3. Sua internet/DNS está funcionando.")
                    print("\n   Dica: Copie a connection string do Render e cole no .env como AIVEN_DATABASE_URL")
                    return 1
                raise

        print("=" * 60)
        print("INICIANDO SEED DE DADOS COMPLETO")
        print("=" * 60)

        # Se apenas testar login
        if args.test_login:
            if test_admin_login():
                return 0
            else:
                return 1

        # 1. Verificar/Resetar banco
        deve_resetar = args.reset

        if not deve_resetar:
            est_existente = db.session.get(Estabelecimento, args.estabelecimento_id)
            if not est_existente:
                print("⚠️ Banco vazio detectado. Iniciando seed...")
                deve_resetar = True
            else:
                print("⚠️ Já existem dados no banco. Use --reset para recriar.")
                print(f"   Estabelecimento: {est_existente.nome_fantasia}")

                # Testar login do admin existente
                test_admin_login()

                return 0

        if deve_resetar:
            reset_database()

        # Debug: Verificar colunas da tabela produtos
        from app.models import Produto
        print(f"DEBUG: Colunas em Produto model: {[c.name for c in Produto.__table__.columns]}")
        
        # Ativar log do SQLAlchemy para debugar o IntegrityError
        import logging
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

        try:
            # 2. Criar estabelecimento e configuração
            est = ensure_estabelecimento(fake, args.estabelecimento_id)
            ensure_configuracao(est.id)

            # 3. Criar funcionários (com verificação de senha embutida)
            funcionarios = seed_funcionarios(fake, est.id)

            # 4. Criar clientes
            clientes = seed_clientes(fake, est.id, n=args.clientes)

            # 5. Criar fornecedores
            fornecedores = seed_fornecedores(fake, est.id, n=args.fornecedores)

            # 6. Criar categorias
            categorias = seed_categorias_produto(fake, est.id)

            # 7. Criar produtos (SEM estoque - quantidade=0)
            produtos = seed_produtos(
                fake, est.id, categorias, fornecedores, n=args.produtos
            )

            # 8. Criar pedidos de compra (PRIMEIRO - isso popula o estoque via lotes)
            seed_pedidos_compra(fake, est.id, funcionarios, fornecedores, produtos)

            # 8.5. Criar lotes de reabastecimento (FIFO com múltiplos lotes por produto)
            seed_lotes_reabastecimento(fake, est.id, funcionarios, fornecedores, produtos)

            # 9. Criar vendas (DEPOIS - agora há estoque disponível)
            is_neon = db.engine.name == "postgresql"
            seed_vendas(
                fake, est.id, funcionarios, clientes, produtos, dias_passados=args.dias,
                neon_safe=is_neon
            )

            # 9.5. Garantir que todos os produtos tenham vendas
            seed_garantir_vendas_todos_produtos(
                fake, est.id, funcionarios, clientes, produtos, neon_safe=is_neon
            )

            # 9.6. Criar histórico de preços (alterações ao longo do tempo)
            seed_historico_precos(fake, est.id, produtos, funcionarios, dias_historico=args.dias)

            # 10. Criar despesas + contas a pagar (módulo financeiro ERP)
            seed_despesas(fake, est.id, fornecedores)

            # 10.5. Criar contas a receber (vendas a prazo)
            seed_contas_receber(est.id, clientes)

            # 11. Criar histórico de ponto (90 dias com cenários variados)
            seed_ponto(fake, est.id, funcionarios, dias_passados=90)

            # 11.5. Criar benefícios e atribuir a funcionários
            seed_beneficios(fake, est.id, funcionarios)

            # 11.6. Calcular banco de horas (baseado nos registros de ponto)
            seed_banco_horas(est.id, funcionarios, meses_passados=3)

            # 11.7. Criar justificativas de ponto
            seed_justificativas(fake, est.id, funcionarios, dias_passados=90)

            # 12. Criar caixas
            seed_caixas(fake, est.id, funcionarios)

            # 13. Criar dashboard métricas
            seed_dashboard_metricas(est.id)

            # 13. Criar relatórios agendados
            seed_relatorios_agendados(fake, est.id)

            # 14. Criar histórico de login
            seed_login_history(fake, est.id, funcionarios)

            # 🔥 VERIFICAÇÃO FINAL: Regras de negócio do seed
            print("\n" + "=" * 60)
            print("🔍 VERIFICAÇÃO FINAL DE INTEGRIDADE")
            print("=" * 60)
            
            hoje = date.today()
            
            # Regra 1: Todo produto DEVE ter pelo menos um PedidoCompraItem
            produtos_sem_pc = []
            for p in produtos:
                tem_pedido = db.session.query(
                    exists().where(PedidoCompraItem.produto_id == p.id)
                ).scalar()
                if not tem_pedido:
                    produtos_sem_pc.append(p)
            
            if produtos_sem_pc:
                print(f"  ❌ FALHA: {len(produtos_sem_pc)} produtos SEM pedido de compra:")
                for p in produtos_sem_pc[:10]:
                    print(f"     - [{p.id}] {p.nome} (fornecedor_id={p.fornecedor_id})")
                print("  → VIOLAÇÃO: Todo produto deve ser oriundo de um pedido de compra!")
                return 1
            else:
                print(f"  ✅ REGRA OK: {len(produtos)}/{len(produtos)} produtos oriundos de pedido de compra (100%)")
            
            # Regra 2: Todo produto DEVE ter fornecedor válido
            produtos_sem_forn = [p for p in produtos if not p.fornecedor_id]
            if produtos_sem_forn:
                print(f"  ❌ FALHA: {len(produtos_sem_forn)} produtos sem fornecedor")
                return 1
            else:
                print(f"  ✅ REGRA OK: {len(produtos)}/{len(produtos)} produtos com fornecedor válido (100%)")
            
            # Regra 3: Todo produto DEVE ter pelo menos um ProdutoLote
            produtos_sem_lote = []
            for p in produtos:
                tem_lote = db.session.query(
                    exists().where(ProdutoLote.produto_id == p.id)
                ).scalar()
                if not tem_lote:
                    produtos_sem_lote.append(p)
            
            if produtos_sem_lote:
                print(f"  ⚠️ AVISO: {len(produtos_sem_lote)} produtos sem lote registrado")
            else:
                print(f"  ✅ REGRA OK: {len(produtos)}/{len(produtos)} produtos com lote (100%)")
            
            # Regra 4: Toda entrada de estoque DEVE estar vinculada a um pedido de compra
            entradas_sem_pc = db.session.query(MovimentacaoEstoque).filter(
                MovimentacaoEstoque.tipo == "entrada",
                MovimentacaoEstoque.pedido_compra_id.is_(None),
            ).count()
            if entradas_sem_pc > 0:
                print(f"  ⚠️ AVISO: {entradas_sem_pc} entradas de estoque sem vínculo com pedido de compra")
            else:
                total_entradas = db.session.query(MovimentacaoEstoque).filter(
                    MovimentacaoEstoque.tipo == "entrada"
                ).count()
                print(f"  ✅ REGRA OK: {total_entradas} entradas de estoque vinculadas a pedidos de compra (100%)")
            
            # Regra 5: Todo produto DEVE ter data_validade e lote (FIFO)
            produtos_sem_validade = [p for p in produtos if not p.data_validade]
            produtos_sem_lote_campo = [p for p in produtos if not p.lote]
            
            if produtos_sem_validade:
                print(f"  ❌ FALHA: {len(produtos_sem_validade)} produtos SEM data_validade!")
                for p in produtos_sem_validade[:5]:
                    print(f"     - [{p.id}] {p.nome}")
                return 1
            else:
                print(f"  ✅ REGRA OK: {len(produtos)}/{len(produtos)} produtos com data_validade (100%)")
            
            if produtos_sem_lote_campo:
                print(f"  ⚠️ AVISO: {len(produtos_sem_lote_campo)} produtos sem campo lote no Produto")
            else:
                print(f"  ✅ REGRA OK: {len(produtos)}/{len(produtos)} produtos com lote (100%)")
            
            # Regra 6: Todo produto DEVE ter pelo menos 1 ProdutoLote ativo
            produtos_sem_lote_tabela = []
            for p in produtos:
                tem_lote = db.session.query(
                    exists().where(
                        db.and_(ProdutoLote.produto_id == p.id, ProdutoLote.ativo == True)
                    )
                ).scalar()
                if not tem_lote:
                    produtos_sem_lote_tabela.append(p)
            
            if produtos_sem_lote_tabela:
                print(f"  ❌ FALHA: {len(produtos_sem_lote_tabela)} produtos sem ProdutoLote ativo!")
                return 1
            else:
                total_lotes = db.session.query(ProdutoLote).filter_by(
                    estabelecimento_id=est.id, ativo=True
                ).count()
                media_lotes = total_lotes / len(produtos) if produtos else 0
                print(f"  ✅ REGRA OK: {total_lotes} lotes ativos (média {media_lotes:.1f} lotes/produto)")
            
            # Regra 7: Verificar distribuição de validade para alertas
            lotes_vencidos = db.session.query(ProdutoLote).filter(
                ProdutoLote.estabelecimento_id == est.id,
                ProdutoLote.ativo == True,
                ProdutoLote.data_validade < hoje,
            ).count()
            lotes_7d = db.session.query(ProdutoLote).filter(
                ProdutoLote.estabelecimento_id == est.id,
                ProdutoLote.ativo == True,
                ProdutoLote.data_validade.between(hoje, hoje + timedelta(days=7)),
            ).count()
            lotes_30d = db.session.query(ProdutoLote).filter(
                ProdutoLote.estabelecimento_id == est.id,
                ProdutoLote.ativo == True,
                ProdutoLote.data_validade.between(hoje + timedelta(days=8), hoje + timedelta(days=30)),
            ).count()
            print(f"  ✅ ALERTAS: {lotes_vencidos} vencidos | {lotes_7d} críticos (≤7d) | {lotes_30d} médios (8-30d)")
            
            # Regra 8: Deve existir histórico de preços (análise de alta/baixa)
            total_hist = db.session.query(HistoricoPrecos).filter_by(
                estabelecimento_id=est.id
            ).count()
            produtos_com_hist = db.session.query(
                db.func.count(db.distinct(HistoricoPrecos.produto_id))
            ).filter_by(estabelecimento_id=est.id).scalar()
            
            if total_hist > 0:
                print(f"  ✅ REGRA OK: {total_hist} registros de histórico de preços para {produtos_com_hist} produtos")
            else:
                print(f"  ⚠️ AVISO: Nenhum histórico de preços encontrado")
            
            # Regra 9: MÓDULO FINANCEIRO - Contas a Pagar (boletos)
            total_cp = db.session.query(ContaPagar).filter_by(
                estabelecimento_id=est.id
            ).count()
            cp_abertos = db.session.query(ContaPagar).filter_by(
                estabelecimento_id=est.id, status="aberto"
            ).count()
            cp_pagos = db.session.query(ContaPagar).filter_by(
                estabelecimento_id=est.id, status="pago"
            ).count()
            cp_vencidos = db.session.query(ContaPagar).filter(
                ContaPagar.estabelecimento_id == est.id,
                ContaPagar.status == "aberto",
                ContaPagar.data_vencimento < hoje,
            ).count()
            
            if total_cp > 0:
                print(f"  ✅ REGRA OK: {total_cp} contas a pagar ({cp_pagos} pagas, {cp_abertos} abertas, {cp_vencidos} vencidas)")
            else:
                print(f"  ⚠️ AVISO: Nenhuma conta a pagar encontrada")
            
            # Regra 10: Contas a Receber (vendas a prazo)
            total_cr = db.session.query(ContaReceber).filter_by(
                estabelecimento_id=est.id
            ).count()
            cr_abertos = db.session.query(ContaReceber).filter_by(
                estabelecimento_id=est.id, status="aberto"
            ).count()
            cr_recebidos = db.session.query(ContaReceber).filter_by(
                estabelecimento_id=est.id, status="recebido"
            ).count()
            cr_inadimplentes = db.session.query(ContaReceber).filter(
                ContaReceber.estabelecimento_id == est.id,
                ContaReceber.status == "aberto",
                ContaReceber.data_vencimento < hoje,
            ).count()
            
            if total_cr > 0:
                print(f"  ✅ REGRA OK: {total_cr} contas a receber ({cr_recebidos} recebidas, {cr_abertos} abertas, {cr_inadimplentes} inadimplentes)")
            else:
                print(f"  ⚠️ AVISO: Nenhuma conta a receber encontrada")
            
            # Regra 11: Despesas devem gerar boletos (forma_pagamento='boleto' → ContaPagar)
            despesas_boleto = db.session.query(Despesa).filter(
                Despesa.estabelecimento_id == est.id,
                Despesa.forma_pagamento == "boleto",
            ).count()
            print(f"  ✅ FINANCEIRO: {despesas_boleto} despesas com pagamento via boleto")
            
            print("=" * 60)

            # 🔥 TESTE FINAL DE LOGIN
            if test_admin_login():
                print("\n" + "=" * 60)
                print("✅ SEED CONCLUÍDO COM SUCESSO TOTAL!")
                print("=" * 60)
                print(f"Estabelecimento: {est.nome_fantasia}")
                print(f"CNPJ: {est.cnpj}")
                print(f"Endereço: {est.endereco_completo()}")
                print("\n👥 USUÁRIOS PARA TESTE:")
                print("  • Administrador: admin / admin123")
                print("  • Caixa: caixa01 / 123456")
                print("  • Estoque: estoque01 / 123456")
                # Contar registros de histórico de preços
                total_hist_precos = db.session.query(HistoricoPrecos).filter_by(
                    estabelecimento_id=est.id
                ).count()
                
                # Contar registros RH
                total_registros_ponto = db.session.query(RegistroPonto).filter_by(
                    estabelecimento_id=est.id
                ).count()
                total_beneficios = db.session.query(FuncionarioBeneficio).count()
                total_banco_horas = db.session.query(BancoHoras).count()
                total_justificativas = db.session.query(JustificativaPonto).filter_by(
                    estabelecimento_id=est.id
                ).count()
                
                # Contar registros financeiros
                total_contas_pagar = db.session.query(ContaPagar).filter_by(
                    estabelecimento_id=est.id
                ).count()
                total_contas_receber = db.session.query(ContaReceber).filter_by(
                    estabelecimento_id=est.id
                ).count()
                total_despesas = db.session.query(Despesa).filter_by(
                    estabelecimento_id=est.id
                ).count()
                
                print("\n📊 DADOS GERADOS:")
                print(f"  • {len(clientes)} clientes")
                print(f"  • {len(fornecedores)} fornecedores")
                print(f"  • {len(produtos)} produtos (100% oriundos de pedidos de compra)")
                print(f"  • Vendas dos últimos {args.dias} dias")
                print(f"  • {total_hist_precos} registros de histórico de preços")
                print(f"\n💰 MÓDULO FINANCEIRO:")
                print(f"  • {total_despesas} despesas (fixas + variáveis + problemáticas)")
                print(f"  • {total_contas_pagar} contas a pagar (boletos de fornecedores + despesas)")
                print(f"  • {total_contas_receber} contas a receber (vendas a prazo)")
                print(f"\n👥 DADOS RH:")
                print(f"  • {total_registros_ponto} registros de ponto (90 dias)")
                print(f"  • {total_beneficios} atribuições de benefícios")
                print(f"  • {total_banco_horas} registros de banco de horas")
                print(f"  • {total_justificativas} justificativas de ponto")
                print("=" * 60)

                return 0
            else:
                print("\n❌ SEED FALHOU - LOGIN DO ADMIN NÃO FUNCIONA")
                print(
                    "   Verifique o model Funcionario e o método set_senha/check_senha"
                )
                return 1

        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO NO SEED: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            try:
                db.engine.dispose()
            except Exception:
                pass
            err_str = str(e).lower()
            if "translate host" in err_str or "name or service not known" in err_str:
                print("\n💡 Dica: Esse erro geralmente indica host/URL errado ou serviço PostgreSQL inativo.")
                print("   Use no .env a MESMA connection string do Render (AIVEN_DATABASE_URL ou DATABASE_URL).")
            return 1


if __name__ == "__main__":
    sys.exit(main())

