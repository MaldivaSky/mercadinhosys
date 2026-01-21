"""
Seed de dados completo para o sistema ERP comercial (compatível com models.py atual).

Objetivos:
- Gerar dados realistas e completos para testar todas as funcionalidades do sistema
- Compatível com SQLite (localhost) e PostgreSQL (nuvem)
- Credenciais de teste: admin / admin123

Uso:
  - `python seed.py --reset` (apaga e recria todos os dados)
  - `python seed.py` (apenas preenche se estiver vazio)

Automaticamente executado no Render pelo Start Command.
"""

from __future__ import annotations

import os
import sys
import argparse
import random
import json
import hashlib  # 🔥 ADICIONADO
from datetime import datetime, timedelta, date, time
from typing import List, Optional, Dict, Any
from decimal import Decimal

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
    print("🧹 Iniciando RESET do banco de dados...")

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
    """Cria funcionários de teste, incluindo admin."""
    print("👥 Criando funcionários...")

    funcionarios_data = [
        {
            "nome": "Administrador Sistema",
            "username": "admin",
            "cpf": fake.cpf(),
            "rg": f"MG-{random.randint(10000000, 99999999)}",
            "data_nascimento": date(1985, 1, 1),
            "telefone": fake.phone_number(),
            "celular": fake.cellphone_number(),
            "email": "admin@empresa.com",
            "cargo": "Gerente",
            "data_admissao": date.today() - timedelta(days=365),
            "salario_base": Decimal("3500.00"),
            "role": "ADMIN",
            "permissoes": {
                "pdv": True,
                "estoque": True,
                "compras": True,
                "financeiro": True,
                "configuracoes": True,
                "relatorios": True,
            },
            "senha": "admin123",
        },
        {
            "nome": fake.name(),
            "username": "caixa01",
            "cpf": fake.cpf(),
            "rg": f"SP-{random.randint(10000000, 99999999)}",
            "data_nascimento": date(1990, 5, 15),
            "telefone": fake.phone_number(),
            "celular": fake.cellphone_number(),
            "email": fake.email(),
            "cargo": "Caixa",
            "data_admissao": date.today() - timedelta(days=180),
            "salario_base": Decimal("1850.00"),
            "role": "FUNCIONARIO",
            "permissoes": {
                "pdv": True,
                "estoque": False,
                "compras": False,
                "financeiro": False,
                "configuracoes": False,
                "relatorios": False,
            },
            "senha": "123456",
        },
        {
            "nome": fake.name(),
            "username": "estoque01",
            "cpf": fake.cpf(),
            "rg": f"RJ-{random.randint(10000000, 99999999)}",
            "data_nascimento": date(1992, 8, 22),
            "telefone": fake.phone_number(),
            "celular": fake.cellphone_number(),
            "email": fake.email(),
            "cargo": "Estoquista",
            "data_admissao": date.today() - timedelta(days=90),
            "salario_base": Decimal("2100.00"),
            "role": "FUNCIONARIO",
            "permissoes": {
                "pdv": True,
                "estoque": True,
                "compras": False,
                "financeiro": False,
                "configuracoes": False,
                "relatorios": False,
            },
            "senha": "123456",
        },
    ]

    funcionarios = []
    for func_data in funcionarios_data:
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
            rg=func_data["rg"],
            data_nascimento=func_data["data_nascimento"],
            telefone=func_data["telefone"],
            celular=func_data["celular"],
            email=func_data["email"],
            cargo=func_data["cargo"],
            data_admissao=func_data["data_admissao"],
            salario_base=func_data["salario_base"],
            role=func_data["role"],
            permissoes_json=json.dumps(func_data["permissoes"]),
            ativo=True,
            foto_url=None,
            cep=fake.postcode(),
            logradouro=fake.street_name(),
            numero=str(random.randint(1, 999)),
            complemento="",
            bairro=fake.bairro(),
            cidade=fake.city(),
            estado=fake.estado_sigla(),
            pais="Brasil",
        )

        # 🔥🔥🔥 CORREÇÃO CRÍTICA: Usar a MESMA lógica do auth.py
        # O auth.py usa hashlib.sha256(f"{senha}{salt}").hexdigest()
        # Vamos replicar EXATAMENTE isso
        senha_plana = func_data["senha"]

        # 1. Se o model tem método set_senha, use-o
        try:
            f.set_senha(senha_plana)
        except:
            # 2. Se não, use a lógica do auth.py
            # Supondo que seu model tem campo 'salt' e armazena hash em 'senha'
            salt = "sistema"  # Isso DEVE ser o mesmo que no seu model!
            senha_hash = hashlib.sha256(f"{senha_plana}{salt}".encode()).hexdigest()

            # Setar diretamente nos campos (ajuste conforme seu model)
            f.senha = senha_hash
            if hasattr(f, "salt"):
                f.salt = salt

        db.session.add(f)
        funcionarios.append(f)

    db.session.commit()

    # 🔥 VERIFICAÇÃO IMEDIATA: Testar se o login funciona
    print("\n🔐 Verificando login do admin...")
    admin = Funcionario.query.filter_by(
        username="admin", estabelecimento_id=estabelecimento_id
    ).first()
    if admin:
        # Testar se a senha funciona
        if hasattr(admin, "check_senha"):
            if admin.check_senha("admin123"):
                print("✅ Admin pode logar com 'admin123'")
            else:
                print("❌ ERRO: Senha do admin NÃO FUNCIONA!")
                print(
                    "   Hash armazenado:",
                    admin.senha[:50] + "..." if admin.senha else "None",
                )
                print("   Salt:", admin.salt if hasattr(admin, "salt") else "Não tem")

                # Calcular hash manualmente para debug
                if hasattr(admin, "salt") and admin.salt:
                    test_hash = hashlib.sha256(
                        f"admin123{admin.salt}".encode()
                    ).hexdigest()
                    print("   Hash calculado:", test_hash[:50] + "...")
                    print("   Hash correto?", admin.senha == test_hash)
        else:
            print("⚠️  Método check_senha não encontrado no model")

    print(f"✅ {len(funcionarios)} funcionários criados")
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
    fake: Faker, estabelecimento_id: int, n: int = 8
) -> List[Fornecedor]:
    """Cria fornecedores de teste."""
    print("🏭 Criando fornecedores...")

    fornecedores = []
    for i in range(n):
        nome_empresa = fake.company()

        # Gerar complemento aleatório
        complementos = ["Galpão 1", "Sede", "Matriz", "Filial", "Depósito", ""]
        complemento = random.choice(complementos) if random.random() > 0.5 else ""

        f = Fornecedor(
            estabelecimento_id=estabelecimento_id,
            nome_fantasia=nome_empresa,
            razao_social=f"{nome_empresa} LTDA",
            cnpj=fake.cnpj(),
            inscricao_estadual=f"ISENTO",
            telefone=fake.phone_number(),
            email=fake.company_email(),
            contato_nome=fake.name(),
            contato_telefone=fake.phone_number(),
            prazo_entrega=random.choice([7, 15, 30, 45]),
            forma_pagamento=random.choice(
                ["30 DIAS", "45 DIAS", "À VISTA", "14/28/42"]
            ),
            classificacao=random.choice(["REGULAR", "PREFERENCIAL", "NOVO"]),
            total_compras=random.randint(0, 50),
            valor_total_comprado=Decimal(str(round(random.uniform(5000, 50000), 2))),
            ativo=random.random() > 0.1,  # 90% ativos
            cep=fake.postcode(),
            logradouro=fake.street_name(),
            numero=str(random.randint(1, 9999)),
            complemento=complemento,
            bairro="Industrial",
            cidade=fake.city(),
            estado=fake.estado_sigla(),
            pais="Brasil",
        )

        db.session.add(f)
        fornecedores.append(f)

    db.session.commit()
    print(f"✅ {len(fornecedores)} fornecedores criados")
    return fornecedores


def seed_categorias_produto(
    fake: Faker, estabelecimento_id: int
) -> List[CategoriaProduto]:
    """Cria categorias de produtos."""
    print("🏷️ Criando categorias de produtos...")

    categorias_data = [
        {"nome": "Bebidas", "descricao": "Refrigerantes, sucos, águas, cervejas"},
        {"nome": "Mercearia", "descricao": "Arroz, feijão, macarrão, óleo"},
        {"nome": "Frios e Laticínios", "descricao": "Queijos, iogurtes, manteiga"},
        {"nome": "Carnes", "descricao": "Bovinas, suínas, aves, peixes"},
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
    for i, (
        nome,
        categoria_nome,
        codigo,
        codigo_barras,
        marca,
        preco_custo,
        preco_venda,
    ) in enumerate(produtos_data):
        categoria = categorias_map.get(categoria_nome)
        if not categoria:
            continue

        # Gerar dados variados
        quantidade = random.randint(10, 100)
        quantidade_minima = max(5, quantidade // 4)
        margem = ((preco_venda - preco_custo) / preco_custo) * 100

        p = Produto(
            estabelecimento_id=estabelecimento_id,
            categoria_id=categoria.id,
            fornecedor_id=random.choice(fornecedores).id if fornecedores else None,
            codigo_barras=codigo_barras,
            codigo_interno=codigo,
            nome=nome,
            descricao=f"{nome} - {marca if marca else 'Produto fresco'}",
            marca=marca if marca else None,
            unidade_medida=random.choice(["UN", "KG", "L", "CX"]),
            quantidade=quantidade,
            quantidade_minima=quantidade_minima,
            preco_custo=Decimal(str(preco_custo)),
            preco_venda=Decimal(str(preco_venda)),
            margem_lucro=Decimal(str(round(margem, 2))),
            ncm="".join([str(random.randint(0, 9)) for _ in range(8)]),
            origem=0,
            total_vendido=0.0,
            quantidade_vendida=0,
            classificacao_abc=random.choice(["A", "B", "C"]),
            controlar_validade=random.random() > 0.5,
            data_validade=(
                date.today() + timedelta(days=random.randint(30, 365))
                if random.random() > 0.3
                else None
            ),
            lote=f"L{random.randint(1000, 9999)}" if random.random() > 0.5 else None,
            imagem_url=None,
            ativo=True,
        )

        db.session.add(p)
        produtos.append(p)

    # Criar produtos adicionais se necessário
    while len(produtos) < n:
        categoria = random.choice(categorias)
        fornecedor = random.choice(fornecedores) if fornecedores else None

        nome = f"Produto Genérico {len(produtos)+1}"
        preco_custo = round(random.uniform(2.0, 50.0), 2)
        preco_venda = round(preco_custo * random.uniform(1.3, 2.0), 2)

        p = Produto(
            estabelecimento_id=estabelecimento_id,
            categoria_id=categoria.id,
            fornecedor_id=fornecedor.id if fornecedor else None,
            codigo_barras=fake.ean13(),
            codigo_interno=f"GEN-{len(produtos)+1:03d}",
            nome=nome,
            descricao=f"Produto genérico para testes",
            marca=fake.company() if random.random() > 0.5 else None,
            unidade_medida=random.choice(["UN", "KG", "L", "CX"]),
            quantidade=random.randint(0, 200),
            quantidade_minima=random.randint(5, 20),
            preco_custo=Decimal(str(preco_custo)),
            preco_venda=Decimal(str(preco_venda)),
            margem_lucro=Decimal(
                str(round(((preco_venda - preco_custo) / preco_custo) * 100, 2))
            ),
            ncm="".join([str(random.randint(0, 9)) for _ in range(8)]),
            origem=0,
            total_vendido=0.0,
            quantidade_vendida=0,
            ativo=random.random() > 0.1,
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
    dias_passados: int = 90,
    vendas_por_dia: tuple = (3, 8),
):
    """Cria vendas realistas com itens e pagamentos."""
    print("🧾 Criando vendas...")

    vendas_criadas = 0
    hoje = date.today()

    # Distribuição horária de vendas (mais vendas entre 10h-19h)
    horarios_pico = [
        (9, 0.5),
        (10, 2),
        (11, 3),
        (12, 4),
        (13, 2),
        (14, 2),
        (15, 2),
        (16, 3),
        (17, 4),
        (18, 3),
        (19, 1),
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

            produtos_venda = random.sample(produtos, min(num_itens, len(produtos)))

            for produto in produtos_venda:
                quantidade = random.randint(1, 3)
                preco_unitario = produto.preco_venda
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
                    custo_unitario=produto.preco_custo,
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

                # Atualizar estoque
                produto.quantidade -= quantidade
                produto.quantidade_vendida += quantidade
                produto.total_vendido += float(total_item)
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
                    custo_unitario=produto.preco_custo,
                    valor_total=produto.preco_custo * Decimal(str(quantidade)),
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
                cliente.total_compras += 1
                cliente.valor_total_gasto += total_venda
                cliente.ultima_compra = data_hora_venda

            vendas_criadas += 1

    db.session.commit()
    print(f"✅ {vendas_criadas} vendas criadas")
    return vendas_criadas


def seed_pedidos_compra(
    fake: Faker,
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    fornecedores: List[Fornecedor],
    produtos: List[Produto],
):
    """Cria pedidos de compra realistas."""
    print("📋 Criando pedidos de compra...")

    pedidos_criados = 0
    hoje = date.today()

    for _ in range(random.randint(5, 15)):
        funcionario = random.choice([f for f in funcionarios if f.cargo != "Caixa"])
        fornecedor = random.choice(fornecedores)

        data_pedido = hoje - timedelta(days=random.randint(1, 60))
        data_previsao = data_pedido + timedelta(days=fornecedor.prazo_entrega)

        pedido = PedidoCompra(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=fornecedor.id,
            funcionario_id=funcionario.id,
            numero_pedido=f"PC{data_pedido.strftime('%Y%m%d')}{pedidos_criados+1:03d}",
            data_pedido=data_pedido,
            data_previsao_entrega=data_previsao,
            data_recebimento=data_previsao if random.random() > 0.3 else None,
            status=random.choice(["pendente", "recebido", "cancelado"]),
            subtotal=Decimal("0.00"),
            desconto=Decimal("0.00"),
            frete=Decimal(str(round(random.uniform(20, 100), 2))),
            total=Decimal("0.00"),
            condicao_pagamento=fornecedor.forma_pagamento,
            numero_nota_fiscal=fake.ean13() if random.random() > 0.5 else None,
            serie_nota_fiscal=(
                str(random.randint(1, 9)) if random.random() > 0.5 else None
            ),
            observacoes=fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
        )

        db.session.add(pedido)
        db.session.flush()

        # Adicionar itens
        produtos_pedido = random.sample(produtos, random.randint(3, 10))
        subtotal_pedido = Decimal("0.00")

        for produto in produtos_pedido:
            quantidade = random.randint(10, 50)
            preco_unitario = produto.preco_custo * Decimal(
                str(random.uniform(0.8, 0.95))
            )  # Compra com desconto
            desconto_percentual = Decimal(
                str(random.uniform(0, 0.1))
            )  # 0-10% de desconto
            total_item = (
                preco_unitario
                * Decimal(str(quantidade))
                * (Decimal("1.00") - desconto_percentual)
            )

            item = PedidoCompraItem(
                pedido_id=pedido.id,
                produto_id=produto.id,
                produto_nome=produto.nome,
                produto_unidade=produto.unidade_medida,
                quantidade_solicitada=quantidade,
                quantidade_recebida=quantidade if pedido.data_recebimento else 0,
                preco_unitario=preco_unitario,
                desconto_percentual=desconto_percentual,
                total_item=total_item,
                status="recebido" if pedido.data_recebimento else "pendente",
            )

            db.session.add(item)
            subtotal_pedido += total_item

            # Se recebido, criar movimentação de estoque
            if pedido.data_recebimento:
                produto.quantidade += quantidade

                mov = MovimentacaoEstoque(
                    estabelecimento_id=estabelecimento_id,
                    produto_id=produto.id,
                    pedido_compra_id=pedido.id,
                    funcionario_id=funcionario.id,
                    tipo="entrada",
                    quantidade=quantidade,
                    quantidade_anterior=produto.quantidade - quantidade,
                    quantidade_atual=produto.quantidade,
                    custo_unitario=preco_unitario,
                    valor_total=total_item,
                    motivo="Compra",
                    observacoes=f"Pedido {pedido.numero_pedido}",
                    created_at=pedido.data_pedido,
                )
                db.session.add(mov)

        # Calcular totais do pedido
        pedido.subtotal = subtotal_pedido
        pedido.desconto = (
            subtotal_pedido * Decimal("0.05")
            if random.random() > 0.7
            else Decimal("0.00")
        )
        pedido.total = pedido.subtotal - pedido.desconto + pedido.frete

        # Atualizar fornecedor
        fornecedor.total_compras += 1
        fornecedor.valor_total_comprado += pedido.total

        pedidos_criados += 1

    db.session.commit()
    print(f"✅ {pedidos_criados} pedidos de compra criados")


def seed_despesas(fake: Faker, estabelecimento_id: int, fornecedores: List[Fornecedor]):
    """Cria despesas fixas e variáveis."""
    print("💸 Criando despesas...")

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

    despesas = []
    hoje = date.today()

    # Despesas fixas
    for despesa_data in despesas_fixas:
        for mes_offset in range(6, -1, -1):  # Últimos 6 meses
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

    # Despesas variáveis
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
    print(f"✅ {len(despesas)} despesas criadas")
    return despesas


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
    parser.add_argument("--clientes", type=int, default=50)
    parser.add_argument("--fornecedores", type=int, default=8)
    parser.add_argument("--produtos", type=int, default=100)
    parser.add_argument("--dias", type=int, default=90)
    parser.add_argument("--test-login", action="store_true", help="Apenas testa login")

    args = parser.parse_args(argv)

    fake = _faker()

    app = create_app(os.getenv("FLASK_ENV", "default"))

    with app.app_context():
        print("=" * 60)
        print("🚀 INICIANDO SEED DE DADOS COMPLETO")
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

            # 7. Criar produtos
            produtos = seed_produtos(
                fake, est.id, categorias, fornecedores, n=args.produtos
            )

            # 8. Criar vendas
            seed_vendas(
                fake, est.id, funcionarios, clientes, produtos, dias_passados=args.dias
            )

            # 9. Criar pedidos de compra
            seed_pedidos_compra(fake, est.id, funcionarios, fornecedores, produtos)

            # 10. Criar despesas
            seed_despesas(fake, est.id, fornecedores)

            # 11. Criar caixas
            seed_caixas(fake, est.id, funcionarios)

            # 12. Criar dashboard métricas
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

