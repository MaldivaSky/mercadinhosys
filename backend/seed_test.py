"""
Seed de dados completo para o sistema ERP comercial (compativel com models.py atual).

Objetivos:
- Gerar dados realistas e completos para testar todas as funcionalidades do sistema
- Compativel com SQLite (localhost) e PostgreSQL (nuvem)
- Credenciais de teste: admin / admin123

Uso:
  - `python seed_test.py --reset --local` (apaga e recria todos os dados localmente)
  - `python seed_test.py --reset` (apaga e recria todos os dados no banco configurado)
  - `python seed_test.py` (apenas preenche se estiver vazio)

Automaticamente executado no Render pelo Start Command.
"""

from __future__ import annotations

import os
import sys
import argparse
import random
import json
import hashlib
from datetime import datetime, timedelta, date, time
from typing import List, Optional, Dict, Any
from decimal import Decimal

# Configurar encoding UTF-8 para evitar problemas de Unicode
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from sqlalchemy import text

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
            # PostgreSQL - usar TRUNCATE CASCADE
            print("  - [PostgreSQL] Limpando dados (TRUNCATE CASCADE)...")

            # Ordem reversa para evitar violações de FK
            tabelas = [
                "movimentacoes_caixa",
                "caixas",
                "login_history",
                "dashboard_metricas",
                "relatorios_agendados",
                "contas_receber",
                "contas_pagar",
                "pedido_compra_itens",
                "pedidos_compra",
                "movimentacoes_estoque",
                "pagamentos",
                "venda_itens",
                "vendas",
                "despesas",
                "produtos",
                "categorias_produto",
                "fornecedores",
                "clientes",
                "funcionarios",
                "configuracoes",
                "estabelecimentos",
            ]

            for tabela in tabelas:
                try:
                    db.session.execute(
                        text(f"TRUNCATE TABLE {tabela} RESTART IDENTITY CASCADE")
                    )
                except Exception as e:
                    print(f"  ⚠️ Tabela {tabela} não existe ou erro: {e}")

            # Garante estrutura atualizada
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

    # FUNCIONÁRIOS DEMITIDOS (25) - com histórico realista
    ex_funcionarios_data = [
        ("Roberto Oliveira", "345.678.901-22", date(1980, 6, 1), date.today() - timedelta(days=450), "Supervisor de Vendas", "Pediu demissão"),
        ("Fernanda Costa", "678.901.234-55", date(1988, 1, 10), date.today() - timedelta(days=200), "Operador de Caixa", "Demitida - faltas"),
        ("Pedro Almeida", "789.012.345-66", date(1992, 8, 5), date.today() - timedelta(days=300), "Repositor", "Pediu demissão"),
        ("Lucas Ferreira", "890.123.456-77", date(1994, 2, 1), date.today() - timedelta(days=550), "Repositor", "Demitido - desempenho"),
        ("Carla Rodrigues", "901.234.567-88", date(1991, 11, 15), date.today() - timedelta(days=100), "Operador de Caixa", "Pediu demissão"),
        ("André Souza", "012.345.678-99", date(1996, 1, 20), date.today() - timedelta(days=250), "Auxiliar Geral", "Demitido - experiência"),
        ("Juliana Pereira", "111.222.333-44", date(1989, 8, 10), date.today() - timedelta(days=600), "Operador de Caixa", "Pediu demissão"),
        ("Marcos Lima", "222.333.444-55", date(1987, 5, 20), date.today() - timedelta(days=750), "Repositor", "Demitido - conflitos"),
        ("Sandra Martins", "333.444.555-66", date(1990, 12, 1), date.today() - timedelta(days=500), "Auxiliar Admin", "Pediu demissão"),
        ("Carlos Eduardo", "444.555.666-77", date(1985, 6, 15), date.today() - timedelta(days=900), "Supervisor", "Demitido - reestruturação"),
        ("Patrícia Lima", "555.666.777-88", date(1993, 3, 10), date.today() - timedelta(days=350), "Operador de Caixa", "Pediu demissão"),
        ("Ricardo Santos", "666.777.888-99", date(1988, 8, 15), date.today() - timedelta(days=650), "Repositor", "Demitido - disciplina"),
        ("Camila Oliveira", "777.888.999-00", date(1997, 6, 20), date.today() - timedelta(days=150), "Auxiliar Limpeza", "Pediu demissão"),
        ("Bruno Silva", "888.999.000-11", date(1991, 11, 5), date.today() - timedelta(days=400), "Operador de Caixa", "Demitido - erro caixa"),
        ("Larissa Costa", "999.000.111-22", date(1999, 2, 14), date.today() - timedelta(days=50), "Repositor", "Pediu demissão"),
        ("Diego Ferreira", "000.111.222-33", date(1986, 9, 20), date.today() - timedelta(days=800), "Auxiliar Geral", "Demitido - faltas"),
        ("Amanda Rodrigues", "111.222.333-45", date(1994, 4, 12), date.today() - timedelta(days=200), "Operador de Caixa", "Pediu demissão"),
        ("Thiago Almeida", "222.333.444-56", date(1989, 1, 25), date.today() - timedelta(days=700), "Repositor", "Demitido - rendimento"),
        ("Vanessa Souza", "333.444.555-67", date(1992, 7, 30), date.today() - timedelta(days=300), "Auxiliar Admin", "Pediu demissão"),
        ("Rafael Martins", "444.555.666-78", date(1995, 9, 15), date.today() - timedelta(days=150), "Operador de Caixa", "Demitido - cliente"),
        ("Gabriela Pereira", "555.666.777-89", date(1998, 5, 8), date.today() - timedelta(days=80), "Repositor", "Pediu demissão"),
        ("Felipe Lima", "666.777.888-90", date(1990, 12, 20), date.today() - timedelta(days=450), "Auxiliar Estoque", "Demitido - negligência"),
        ("Natália Santos", "777.888.999-01", date(1996, 8, 3), date.today() - timedelta(days=200), "Operador de Caixa", "Pediu demissão"),
        ("Gustavo Oliveira", "888.999.000-12", date(1988, 11, 12), date.today() - timedelta(days=650), "Repositor", "Demitido - pontualidade"),
        ("Priscila Silva", "999.000.111-23", date(1997, 3, 22), date.today() - timedelta(days=100), "Auxiliar Limpeza", "Pediu demissão"),
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
    print(f"✅ Total: {len(funcionarios)} registros de RH")
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

    produtos_data = [
        # Bebidas
        (
            "Coca-Cola 2L",
            "Bebidas",
            "COC-001",
            "7894900010015",
            "Coca-Cola",
            6.50,
            10.90,
        ),
        (
            "Guaraná Antarctica 2L",
            "Bebidas",
            "GUA-001",
            "7891991000853",
            "Ambev",
            5.80,
            9.90,
        ),
        (
            "Água Mineral 500ml",
            "Bebidas",
            "AGU-001",
            "7892840822941",
            "Crystal",
            1.20,
            2.50,
        ),
        (
            "Suco Del Vale 1L",
            "Bebidas",
            "SCO-001",
            "7891098000251",
            "Del Valle",
            3.50,
            6.90,
        ),
        # Mercearia
        (
            "Arroz Tio João 5kg",
            "Mercearia",
            "ARR-001",
            "7896006741025",
            "Tio João",
            22.00,
            29.90,
        ),
        (
            "Feijão Carioca 1kg",
            "Mercearia",
            "FEI-001",
            "7896079001015",
            "Camil",
            6.50,
            9.90,
        ),
        (
            "Macarrão Espaguete 500g",
            "Mercearia",
            "MAC-001",
            "7896051110223",
            "Renata",
            3.20,
            5.90,
        ),
        (
            "Óleo de Soja 900ml",
            "Mercearia",
            "OLE-001",
            "7898909987042",
            "Liza",
            5.90,
            8.90,
        ),
        # Frios
        (
            "Queijo Mussarela 1kg",
            "Frios e Laticínios",
            "QUE-001",
            "7891000055502",
            "Itambé",
            28.00,
            42.90,
        ),
        (
            "Presunto Sadia 500g",
            "Frios e Laticínios",
            "PRE-001",
            "7893000415101",
            "Sadia",
            12.50,
            19.90,
        ),
        (
            "Iogurte Natural 1L",
            "Frios e Laticínios",
            "IOG-001",
            "7891072001308",
            "Nestlé",
            8.90,
            14.90,
        ),
        # Carnes
        ("Carne Bovina Alcatra 1kg", "Carnes", "CAR-001", None, "Friboi", 38.00, 59.90),
        ("Peito de Frango 1kg", "Carnes", "FRN-001", None, "Seara", 15.90, 24.90),
        ("Linguiça Toscana 500g", "Carnes", "LIN-001", None, "Perdigão", 11.90, 18.90),
        # Higiene
        (
            "Sabonete Dove 90g",
            "Higiene Pessoal",
            "SAB-001",
            "7891150037605",
            "Dove",
            2.50,
            4.90,
        ),
        (
            "Shampoo Clear 200ml",
            "Higiene Pessoal",
            "SHA-001",
            "7891150054664",
            "Clear",
            12.90,
            22.90,
        ),
        (
            "Creme Dental Colgate 90g",
            "Higiene Pessoal",
            "CRE-001",
            "7891021008203",
            "Colgate",
            3.90,
            7.90,
        ),
        # Limpeza
        (
            "Detergente Ypê 500ml",
            "Limpeza",
            "DET-001",
            "7891024113405",
            "Ypê",
            1.90,
            3.90,
        ),
        (
            "Água Sanitária Qboa 1L",
            "Limpeza",
            "SAN-001",
            "7896094908015",
            "Qboa",
            4.90,
            8.90,
        ),
        (
            "Desinfetante Veja 500ml",
            "Limpeza",
            "DES-001",
            "7891024023117",
            "Veja",
            6.90,
            12.90,
        ),
        # Padaria
        ("Pão Francês kg", "Padaria", "PAO-001", None, None, 8.90, 15.90),
        (
            "Biscoito Maizena 400g",
            "Padaria",
            "BIS-001",
            "7891000315504",
            "Marilan",
            3.90,
            7.90,
        ),
        # Hortifrúti
        ("Banana Prata kg", "Hortifrúti", "BAN-001", None, None, 3.90, 7.90),
        ("Tomate kg", "Hortifrúti", "TOM-001", None, None, 4.90, 9.90),
        ("Alface Un", "Hortifrúti", "ALF-001", None, None, 1.50, 3.50),
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
            "aurora alimentos", "p&g", "yoki", "heinz"
        ]:
            marca_fornecedor_map[fornecedor.nome_fantasia.lower()] = fornecedor.id
    
    # Lista de produtos reais conhecidos no Brasil
    produtos_reais = [
        # Bebidas
        ("Coca-Cola 2L", "Bebidas", "COC-001", "7894900010015", "Coca-Cola", 7.50, 11.90),
        ("Guaraná Antarctica 2L", "Bebidas", "GUA-001", "7891991000853", "Ambev", 6.80, 10.90),
        ("Pepsi 2L", "Bebidas", "PEP-001", "7892840800000", "PepsiCo", 6.50, 9.90),
        ("Cerveja Skol 350ml", "Bebidas", "SKO-001", "7891149103100", "Ambev", 2.80, 4.50),
        ("Cerveja Heineken 330ml", "Bebidas", "HEI-001", "7896045500000", "Heineken", 4.50, 7.90),
        ("Água Mineral Crystal 500ml", "Bebidas", "AGU-001", "7892840822941", "Crystal", 1.20, 3.00),
        ("Suco Del Valle Uva 1L", "Bebidas", "SCO-001", "7891098000251", "Del Valle", 4.50, 8.90),
        ("Cerveja Brahma 350ml", "Bebidas", "BRA-001", "7891149103105", "Ambev", 2.70, 4.40),
        ("Energético Red Bull 250ml", "Bebidas", "RED-001", "9002490100070", "Ambev", 6.50, 10.50),
        ("Vinho Tinto Concha y Toro 750ml", "Bebidas", "VIN-001", "7804300101416", "Distribuidor Local 1", 25.00, 42.00),
        ("Vinho Cabernet Sauvignon Tinto Concha y Toro 750ml", "Bebidas", "VIN-002", "7804300101417", "Distribuidor Local 1", 25.00, 42.00),
        ("Vinho Merlot Tinto Concha y Toro 750ml", "Bebidas", "VIN-003", "7804350101418", "Distribuidor Local 1", 25.00, 42.00),
        ("Vinho Pinot Noir Tinto Concha y Toro 750ml", "Bebidas", "VIN-004", "7804800101419", "Distribuidor Local 2", 25.00, 42.00),
        ("Vinho Camernere Tinto Concha y Toro 750ml", "Bebidas", "VIN-005", "7804900101330", "Distribuidor Local 3", 25.00, 42.00),
        ("Vinho Cabernet Branco Concha y Toro 750ml", "Bebidas", "VIN-006", "7804700101410", "Distribuidor Local 4", 25.00, 42.00),
        ("Vinho Sauvignon Branco Concha y Toro 750ml", "Bebidas", "VIN-007", "7804500101411", "Distribuidor Local 1", 25.00, 42.00),


        # Mercearia
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

        # Frios e Laticínios
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

        # Higiene Pessoal
        ("Sabonete Dove Original 90g", "Higiene Pessoal", "SAB-001", "7891150037605", "Dove", 3.50, 5.90),
        ("Pasta de Dente Colgate Total 12", "Higiene Pessoal", "PAS-001", "7891024035000", "Colgate", 6.50, 12.90),
        ("Papel Higiênico Neve 12un", "Higiene Pessoal", "PAP-001", "7891150000000", "Neve", 18.00, 29.90),
        ("Shampoo Pantene 400ml", "Higiene Pessoal", "SHA-002", "7891000000012", "P&G", 15.50, 25.90),
        ("Desodorante Rexona Aerosol", "Higiene Pessoal", "DESO-001", "7891000000013", "Unilever", 12.50, 18.90),
        ("Escova de Dente Oral-B", "Higiene Pessoal", "ESC-001", "7891000000014", "P&G", 8.50, 14.90),
        ("Fio Dental Colgate", "Higiene Pessoal", "FIO-001", "7891000000015", "Colgate", 5.50, 9.90),
        ("Absorvente Always", "Higiene Pessoal", "ABS-001", "7891000000016", "P&G", 7.50, 12.90),

        # Limpeza
        ("Detergente Ypê Neutro 500ml", "Limpeza", "DET-001", "7891024113405", "Ypê", 2.20, 3.90),
        ("Sabão em Pó Omo 800g", "Limpeza", "OMO-001", "7891150000001", "Omo", 12.50, 19.90),
        ("Amaciante Confort 1L", "Limpeza", "AMA-001", "7891150000002", "Confort", 14.50, 22.90),
        ("Água Sanitária Qboa 1L", "Limpeza", "SAN-001", "7896094908015", "Qboa", 5.50, 8.90),
        # Carnes e Hortifrúti
        ("Contra Filé Bovino kg", "Carnes", "CAR-001", None, "Friboi", 45.00, 69.90),
        ("Filé de Peito Frango kg", "Carnes", "FRA-001", None, "Seara", 18.00, 28.90),
        ("Linguiça Toscana Na Brasa kg", "Carnes", "LIN-001", None, "Perdigão", 16.00, 24.90),
        ("Banana Prata kg", "Hortifrúti", "BAN-001", None, "Distribuidor Local 1", 4.50, 8.90),
        ("Tomate Italiano kg", "Hortifrúti", "TOM-001", None, "Distribuidor Local 2", 6.50, 12.90),
        ("Batata Lavada kg", "Hortifrúti", "BAT-001", None, "Distribuidor Local 3", 4.50, 8.90),
        ("Cebola kg", "Hortifrúti", "CEB-001", None, "Distribuidor Local 4", 3.50, 6.90),
        ("Ovos Brancos Dúzia", "Hortifrúti", "OVO-001", None, "Distribuidor Local 5", 8.00, 14.90),
        
        # Pet Shop
        ("Ração Canina", "Pet Shop", "RAO-001", None, "Distribuidor Local 6", 12.00, 18.90),
        ("Ração Felina", "Pet Shop", "RAF-001", None, "Distribuidor Local 7", 15.00, 22.90),
        ("Cama de Pet", "Pet Shop", "CAM-001", None, "Distribuidor Local 8", 25.00, 38.90),
        ("Brinquedo de Pet", "Pet Shop", "BRE-001", None, "Distribuidor Local 9", 10.00, 16.90),
        ("Collar de Pet", "Pet Shop", "COL-001", None, "Distribuidor Local 10", 5.00, 8.90),
        ("Fita Dental de Pet", "Pet Shop", "FIT-001", None, "Distribuidor Local 11", 8.00, 14.90),
        ("Escova de Dente de Pet", "Pet Shop", "ESC-PET-001", None, "Distribuidor Local 12", 12.00, 18.90),
        ("Fio Dental de Pet", "Pet Shop", "FIO-PET-001", None, "Distribuidor Local 13", 15.00, 22.90),
        ("Absorvente de Pet", "Pet Shop", "ABS-PET-001", None, "Distribuidor Local 14", 25.00, 38.90),
        ("Biscoito de Pet", "Pet Shop", "BIS-PET-001", None, "Distribuidor Local 15", 10.00, 16.90),

        # Beleza e Saúde
        ("Shampoo para Cabelo", "Beleza e Saúde", "SHA-001", None, "Distribuidor Local 16", 12.00, 18.90),
        ("Creme para Pele", "Beleza e Saúde", "CRE-001", None, "Distribuidor Local 17", 15.00, 22.90),
        ("Escova de Dente", "Beleza e Saúde", "ESC-BEZ-001", None, "Distribuidor Local 18", 25.00, 38.90),
        ("Fio Dental", "Beleza e Saúde", "FIO-BEZ-001", None, "Distribuidor Local 19", 10.00, 16.90),
        ("Absorvente", "Beleza e Saúde", "ABS-BEZ-001", None, "Distribuidor Local 20", 25.00, 38.90),
        ("Biscoito", "Beleza e Saúde", "BIS-BEZ-001", None, "Distribuidor Local 21", 10.00, 16.90),


        # Padaria
        ("Pão Francês kg", "Padaria", "PAO-001", None, "Distribuidor Local 6", 12.00, 18.90),
        ("Biscoito Trakinas", "Padaria", "BIS-001", "7896000000001", "Mondelez", 3.50, 5.90),
    ]

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

        # Gerar dados variados
        quantidade = random.randint(500, 1000)  # Aumentado de 20-200 para 500-1000
        quantidade_minima = max(10, quantidade // 10)  # Reduzido para 10% em vez de 25%
        # Garantir custo positivo para evitar divisão por zero
        preco_custo_val = float(preco_custo) if preco_custo and float(preco_custo) > 0 else 1.0
        preco_venda_val = float(preco_venda)
        
        margem = ((preco_venda_val - preco_custo_val) / preco_custo_val) * 100
        # Limitar margem para caber no Numeric(5, 2) das models (max 999.99)
        margem = max(0, min(999.99, margem))

        # DATA DE VALIDADE - Focar em 2025 e 2026
        ano_validade = random.choice([2025, 2026])
        mes_validade = random.randint(1, 12)
        dia_validade = random.randint(1, 28)
        data_validade = date(ano_validade, mes_validade, dia_validade)
        
        # Alguns produtos vencidos ou quase vencendo (2025 já passou ou está perto)
        if random.random() < 0.2:
            data_validade = date.today() + timedelta(days=random.randint(-30, 60))

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
            data_validade=data_validade,
            lote=f"L{random.randint(1000, 9999)}",  # OBRIGATÓRIO
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
):
    """Cria vendas realistas com itens e pagamentos."""
    print("🧾 Criando vendas...")

    vendas_criadas = 0
    hoje = date.today()

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

        # Menos vendas em finais de semana
        if data_venda.weekday() >= 5:  # Sábado ou domingo
            min_vendas, max_vendas = max(1, vendas_por_dia[0] - 2), max(
                3, vendas_por_dia[1] - 3
            )
        else:
            min_vendas, max_vendas = vendas_por_dia

        num_vendas = random.randint(min_vendas, max_vendas)

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

            # Criar venda
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

            # Criar itens da venda
            num_itens = random.randint(1, 8)
            subtotal = Decimal("0.00")

            # DISTRIBUIÇÃO DE PARETO: 80% das vendas vêm de 20% dos produtos
            # Selecionar produtos com probabilidade ponderada (alguns produtos vendem muito mais)
            if random.random() < 0.80:  # 80% das vendas
                # Usar os 20% dos produtos mais populares
                num_produtos_populares = max(1, len(produtos) // 5)
                produtos_populares = produtos[:num_produtos_populares]
                produtos_venda = random.choices(produtos_populares, k=min(num_itens, len(produtos_populares)))
            else:  # 20% das vendas
                # Usar produtos aleatórios (incluindo os menos populares)
                produtos_venda = random.sample(produtos, min(num_itens, len(produtos)))

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

    db.session.commit()
    print(f"✅ {vendas_criadas} vendas criadas")
    return vendas_criadas


def seed_garantir_vendas_todos_produtos(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    clientes: List[Cliente],
    produtos: List[Produto],
):
    """Garante que TODOS os produtos tenham pelo menos uma venda registrada.
    Mantém a distribuição de Pareto: produtos populares vendem muito, produtos menos populares vendem pouco."""
    print("🔄 Garantindo que todos os produtos tenham vendas com distribuição de Pareto...")

    produtos_sem_venda = [p for p in produtos if not p.ultima_venda or p.quantidade_vendida == 0]
    
    if not produtos_sem_venda:
        print(f"✅ Todos os {len(produtos)} produtos já têm vendas")
        return

    print(f"⚠️  {len(produtos_sem_venda)} produtos sem vendas - criando vendas para eles...")

    hoje = date.today()
    funcionario = random.choice([f for f in funcionarios if f.ativo])
    
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
            
            # Atualizar produto - usar Decimal e depois converter para float para o banco
            produto.quantidade_vendida = (produto.quantidade_vendida or 0) + quantidade
            produto.total_vendido = float(Decimal(str(produto.total_vendido or 0)) + total_item)
            produto.ultima_venda = data_hora_venda
            
            # Criar movimentação
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
    
    db.session.commit()
    print(f"✅ {len(produtos_sem_venda)} produtos agora têm vendas registradas com distribuição de Pareto")


def seed_pedidos_compra(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    fornecedores: List[Fornecedor],
    produtos: List[Produto],
):
    # Garantir que TODOS os produtos tenham pelo menos um pedido de compra
    print("📦 Garantindo pedidos de compra para todos os produtos...")
    
    hoje = date.today()
    pedidos_criados = 0
    lotes_criados = 0
    boletos_criados = 0
    
    # Agrupar produtos por fornecedor
    produtos_por_fornecedor = {}
    for p in produtos:
        if p.fornecedor_id not in produtos_por_fornecedor:
            produtos_por_fornecedor[p.fornecedor_id] = []
        produtos_por_fornecedor[p.fornecedor_id].append(p)
    
    for forn_id, produtos_forn in produtos_por_fornecedor.items():
        fornecedor = db.session.get(Fornecedor, forn_id)
        if not fornecedor:
            continue
            
        funcionario = random.choice([f for f in funcionarios if f.cargo != "Operador de Caixa"])
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
            
            # Movimentação e estoque
            produto.quantidade += quantidade
            mov = MovimentacaoEstoque(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                pedido_compra_id=pedido.id,
                funcionario_id=funcionario.id,
                tipo="entrada",
                quantidade=quantidade,
                quantidade_anterior=0,
                quantidade_atual=quantidade,
                custo_unitario=preco_compra,
                valor_total=total_item,
                motivo="Entrada Inicial",
                created_at=data_pedido,
            )
            db.session.add(mov)
            
            # Lotes
            lote = ProdutoLote(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                pedido_compra_id=pedido.id,
                fornecedor_id=fornecedor.id,
                numero_lote=f"L{data_pedido.strftime('%Y%m')}{lotes_criados+1:04d}",
                quantidade_inicial=quantidade,
                quantidade=quantidade,
                data_validade=hoje + timedelta(days=random.randint(200, 500)),
                data_entrada=data_pedido,
                preco_custo_unitario=preco_compra,
                ativo=True,
            )
            db.session.add(lote)
            lotes_criados += 1

        pedido.subtotal = subtotal_pedido
        pedido.total = subtotal_pedido
        fornecedor.total_compras += 1
        fornecedor.valor_total_comprado += subtotal_pedido
        pedidos_criados += 1
        
        # Gerar conta a pagar para este pedido
        data_vencimento = data_pedido + timedelta(days=30)
        boleto = ContaPagar(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=fornecedor.id,
            pedido_compra_id=pedido.id,
            numero_documento=f"FAT{pedido.numero_pedido}",
            tipo_documento="duplicata",
            valor_original=pedido.total,
            valor_pago=pedido.total,
            valor_atual=0,
            data_emissao=data_pedido,
            data_vencimento=data_vencimento,
            data_pagamento=data_vencimento,
            status="pago",
            forma_pagamento="transferencia",
        )
        db.session.add(boleto)
        boletos_criados += 1
    
    db.session.commit()
    print(f"✅ Pedidos de compra, lotes e boletos criados para TODOS os {len(produtos)} produtos")


def seed_despesas(fake: Faker, estabelecimento_id: int, fornecedores: List[Fornecedor]):
    """Cria despesas fixas, variáveis e DESNECESSÁRIAS para teste do sistema."""
    print("💸 Criando despesas (incluindo desnecessárias)...")

    despesas_fixas = [
        {
            "descricao": "Aluguel",
            "categoria": "Aluguel",
            "valor": 2500.00,
            "tipo": "fixa",
            "recorrente": True,
        },
        {
            "descricao": "Energia Elétrica",
            "categoria": "Energia",
            "valor": 800.00,
            "tipo": "fixa",
            "recorrente": True,
        },
        {
            "descricao": "Água e Esgoto",
            "categoria": "Água",
            "valor": 300.00,
            "tipo": "fixa",
            "recorrente": True,
        },
        {
            "descricao": "Internet",
            "categoria": "Telecomunicações",
            "valor": 150.00,
            "tipo": "fixa",
            "recorrente": True,
        },
        {
            "descricao": "Salários",
            "categoria": "Pessoal",
            "valor": 7500.00,
            "tipo": "fixa",
            "recorrente": True,
        },
    ]
    
    # 🔥 DESPESAS DESNECESSÁRIAS/PROBLEMÁTICAS para o sistema detectar
    despesas_problematicas = [
        {
            "descricao": "Assinatura de revista de fofocas",
            "categoria": "Outros",
            "valor": 89.90,
            "tipo": "variavel",
            "recorrente": True,
        },
        {
            "descricao": "Decoração de Natal fora de época",
            "categoria": "Marketing",
            "valor": 1200.00,
            "tipo": "variavel",
            "recorrente": False,
        },
        {
            "descricao": "Almoço executivo em restaurante caro",
            "categoria": "Alimentação",
            "valor": 450.00,
            "tipo": "variavel",
            "recorrente": False,
        },
        {
            "descricao": "Curso de astrologia empresarial",
            "categoria": "Treinamento",
            "valor": 890.00,
            "tipo": "variavel",
            "recorrente": False,
        },
        {
            "descricao": "Plantas ornamentais de luxo",
            "categoria": "Outros",
            "valor": 650.00,
            "tipo": "variavel",
            "recorrente": False,
        },
        {
            "descricao": "Assinatura de streaming premium",
            "categoria": "Outros",
            "valor": 55.90,
            "tipo": "variavel",
            "recorrente": True,
        },
        {
            "descricao": "Consultoria de feng shui",
            "categoria": "Consultoria",
            "valor": 1500.00,
            "tipo": "variavel",
            "recorrente": False,
        },
    ]

    despesas = []
    hoje = date.today()

    # Despesas fixas (últimos 6 meses)
    for despesa_data in despesas_fixas:
        for mes_offset in range(6, -1, -1):
            data_despesa = hoje - timedelta(days=30 * mes_offset)

            d = Despesa(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=(
                    random.choice(fornecedores).id
                    if fornecedores and random.random() > 0.5
                    else None
                ),
                descricao=despesa_data["descricao"],
                categoria=despesa_data["categoria"],
                tipo=despesa_data["tipo"],
                valor=Decimal(
                    str(despesa_data["valor"] * random.uniform(0.9, 1.1))
                ),  # Variação de 10%
                data_despesa=data_despesa,
                forma_pagamento=random.choice(
                    ["pix", "dinheiro", "transferencia", "boleto"]
                ),
                recorrente=despesa_data["recorrente"],
                observacoes=None,
            )

            db.session.add(d)
            despesas.append(d)
    
    # 🔥 Despesas problemáticas (últimos 3 meses)
    for despesa_data in despesas_problematicas:
        # Se é recorrente, criar para os últimos 3 meses
        if despesa_data["recorrente"]:
            for mes_offset in range(3, -1, -1):
                data_despesa = hoje - timedelta(days=30 * mes_offset)
                
                d = Despesa(
                    estabelecimento_id=estabelecimento_id,
                    fornecedor_id=None,  # Despesas problemáticas geralmente sem fornecedor
                    descricao=despesa_data["descricao"],
                    categoria=despesa_data["categoria"],
                    tipo=despesa_data["tipo"],
                    valor=Decimal(str(despesa_data["valor"])),
                    data_despesa=data_despesa,
                    forma_pagamento=random.choice(["cartao_credito", "pix"]),
                    recorrente=True,
                    observacoes="⚠️ Despesa questionável",
                )
                db.session.add(d)
                despesas.append(d)
        else:
            # Despesa única nos últimos 90 dias
            data_despesa = hoje - timedelta(days=random.randint(1, 90))
            
            d = Despesa(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=None,
                descricao=despesa_data["descricao"],
                categoria=despesa_data["categoria"],
                tipo=despesa_data["tipo"],
                valor=Decimal(str(despesa_data["valor"])),
                data_despesa=data_despesa,
                forma_pagamento=random.choice(["cartao_credito", "dinheiro"]),
                recorrente=False,
                observacoes="⚠️ Despesa questionável",
            )
            db.session.add(d)
            despesas.append(d)

    # Despesas variáveis normais
    categorias_variaveis = [
        "Manutenção",
        "Material de Escritório",
        "Marketing",
        "Transporte",
        "Outros",
    ]

    for _ in range(20):
        data_despesa = hoje - timedelta(days=random.randint(1, 180))

        d = Despesa(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=(
                random.choice(fornecedores).id
                if fornecedores and random.random() > 0.3
                else None
            ),
            descricao=fake.text(max_nb_chars=30),
            categoria=random.choice(categorias_variaveis),
            tipo="variavel",
            valor=Decimal(str(round(random.uniform(50, 500), 2))),
            data_despesa=data_despesa,
            forma_pagamento=random.choice(["pix", "dinheiro", "cartao_credito"]),
            recorrente=False,
            observacoes=fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
        )

        db.session.add(d)
        despesas.append(d)

    db.session.commit()
    print(f"✅ {len(despesas)} despesas criadas (incluindo {len(despesas_problematicas)} problemáticas)")
    return despesas


def seed_ponto(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    dias_passados: int = 30
):
    """Cria histórico realista de registros de ponto"""
    print("⏰ Criando histórico de ponto...")
    
    from app.models import RegistroPonto, ConfiguracaoHorario
    
    # Criar configuração de horários se não existir
    config = ConfiguracaoHorario.query.filter_by(
        estabelecimento_id=estabelecimento_id
    ).first()
    
    if not config:
        config = ConfiguracaoHorario(
            estabelecimento_id=estabelecimento_id,
            hora_entrada=datetime.strptime('08:00', '%H:%M').time(),
            hora_saida_almoco=datetime.strptime('12:00', '%H:%M').time(),
            hora_retorno_almoco=datetime.strptime('13:00', '%H:%M').time(),
            hora_saida=datetime.strptime('18:00', '%H:%M').time(),
            tolerancia_entrada=10,
            tolerancia_saida_almoco=5,
            tolerancia_retorno_almoco=10,
            tolerancia_saida=5,
            exigir_foto=True,
            exigir_localizacao=False,
            raio_permitido_metros=100
        )
        db.session.add(config)
        db.session.flush()
    
    # Criar registros apenas para funcionários (não para clientes)
    funcionarios_filtrados = [f for f in funcionarios if f.role in ['ADMIN', 'FUNCIONARIO']]
    
    if not funcionarios_filtrados:
        print("   ⚠️  Nenhum funcionário para criar ponto")
        return 0
    
    pontos_criados = 0
    hoje = date.today()
    
    for dias_atras in range(dias_passados, 0, -1):
        data_registro = hoje - timedelta(days=dias_atras)
        
        # Pular fins de semana
        if data_registro.weekday() >= 5:  # 5=sábado, 6=domingo
            continue
        
        for funcionario in funcionarios_filtrados:
            # Entrada (entre 07:50 e 08:15)
            hora_entrada = datetime.strptime('08:00', '%H:%M').time()
            minutos_variacao = random.randint(-10, 15)
            hora_entrada = (
                datetime.combine(data_registro, hora_entrada) + 
                timedelta(minutes=minutos_variacao)
            ).time()
            
            entrada = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_entrada,
                tipo_registro='entrada',
                status='normal' if minutos_variacao <= 10 else 'atrasado',
                minutos_atraso=max(0, minutos_variacao - 10),
                observacao='Entrada matinal'
            )
            db.session.add(entrada)
            pontos_criados += 1
            
            # Saída almoço (entre 11:55 e 12:10)
            hora_saida_alm = datetime.strptime('12:00', '%H:%M').time()
            minutos_var_alm = random.randint(-5, 10)
            hora_saida_alm = (
                datetime.combine(data_registro, hora_saida_alm) + 
                timedelta(minutes=minutos_var_alm)
            ).time()
            
            saida_almoco = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_saida_alm,
                tipo_registro='saida_almoco',
                status='normal',
                minutos_atraso=0,
                observacao='Saída para almoço'
            )
            db.session.add(saida_almoco)
            pontos_criados += 1
            
            # Retorno almoço (entre 12:55 e 13:15)
            hora_retorno_alm = datetime.strptime('13:00', '%H:%M').time()
            minutos_var_ret = random.randint(-5, 15)
            hora_retorno_alm = (
                datetime.combine(data_registro, hora_retorno_alm) + 
                timedelta(minutes=minutos_var_ret)
            ).time()
            
            retorno_almoco = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_retorno_alm,
                tipo_registro='retorno_almoco',
                status='normal' if minutos_var_ret <= 10 else 'atrasado',
                minutos_atraso=max(0, minutos_var_ret - 10),
                observacao='Retorno do almoço'
            )
            db.session.add(retorno_almoco)
            pontos_criados += 1
            
            # Saída final (entre 17:50 e 18:30)
            hora_saida_fim = datetime.strptime('18:00', '%H:%M').time()
            minutos_var_fim = random.randint(-10, 30)
            hora_saida_fim = (
                datetime.combine(data_registro, hora_saida_fim) + 
                timedelta(minutes=minutos_var_fim)
            ).time()
            
            saida = RegistroPonto(
                funcionario_id=funcionario.id,
                estabelecimento_id=estabelecimento_id,
                data=data_registro,
                hora=hora_saida_fim,
                tipo_registro='saida',
                status='normal',
                minutos_atraso=0,
                observacao='Saída final'
            )
            db.session.add(saida)
            pontos_criados += 1
    
    db.session.commit()
    print(f"✅ {pontos_criados} registros de ponto criados")
    return pontos_criados


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
                f"   Hash armazenado: {admin.senha[:50]}..."
                if admin.senha
                else "Nenhum hash"
            )
            print(f"   Salt: {admin.salt}" if hasattr(admin, "salt") else "Sem salt")

            # Calcular hash manualmente para debug
            if hasattr(admin, "salt") and admin.salt:
                test_hash = hashlib.sha256(f"admin123{admin.salt}".encode()).hexdigest()
                print(f"   Hash calculado: {test_hash[:50]}...")
                print(f"   Hash correto? {admin.senha == test_hash}")

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
    parser.add_argument("--clientes", type=int, default=100)
    parser.add_argument("--fornecedores", type=int, default=50)
    parser.add_argument("--produtos", type=int, default=200)
    parser.add_argument("--dias", type=int, default=180)
    parser.add_argument("--test-login", action="store_true", help="Apenas testa login")
    parser.add_argument("--local", action="store_true", help="Popula APENAS banco local (SQLite)")

    args = parser.parse_args(argv)

    fake = _faker()

    if args.local:
        # Remover variáveis de ambiente que apontam para bancos externos
        for key in ["NEON_DATABASE_URL", "DATABASE_URL_TARGET", "DB_PRIMARY", "DATABASE_URL", "POSTGRES_URL"]:
            if key in os.environ:
                del os.environ[key]
        print("Modo LOCAL: Populando APENAS SQLite")

    app = create_app(os.getenv("FLASK_ENV", "default"))

    with app.app_context():
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

            # 9. Criar vendas (DEPOIS - agora há estoque disponível)
            seed_vendas(
                fake, est.id, funcionarios, clientes, produtos, dias_passados=args.dias
            )

            # 9.5. Garantir que todos os produtos tenham vendas
            seed_garantir_vendas_todos_produtos(fake, est.id, funcionarios, clientes, produtos)

            # 10. Criar despesas
            seed_despesas(fake, est.id, fornecedores)

            # 11. Criar histórico de ponto
            seed_ponto(fake, est.id, funcionarios, dias_passados=30)

            # 12. Criar caixas
            seed_caixas(fake, est.id, funcionarios)

            # 13. Criar dashboard métricas
            seed_dashboard_metricas(est.id)

            # 13. Criar relatórios agendados
            seed_relatorios_agendados(fake, est.id)

            # 14. Criar histórico de login
            seed_login_history(fake, est.id, funcionarios)

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
                print("\n📊 DADOS GERADOS:")
                print(f"  • {len(clientes)} clientes")
                print(f"  • {len(fornecedores)} fornecedores")
                print(f"  • {len(produtos)} produtos")
                print(f"  • Vendas dos últimos {args.dias} dias")
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
            return 1


if __name__ == "__main__":
    sys.exit(main())

