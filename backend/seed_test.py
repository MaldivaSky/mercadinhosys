"""Seed de dados fictícios para testes (dashboard + relatórios + despesas).

Objetivos:
- Gerar dados realistas e suficientes para alimentar:
  - dashboard avançado (tendências, sazonalidade, hora pico, top produtos)
  - relatórios (vendas/estoque/clientes/financeiro)
  - módulo de despesas

Uso:
  - `python seed_test.py --reset` (local)
  - No Render, roda automático pelo Start Command.
"""

from __future__ import annotations

import os
import sys
import argparse
import random
from datetime import datetime, timedelta, date
from typing import List, Optional

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker

from app import create_app
from app.models import (
    db,
    Estabelecimento,
    Configuracao,
    Funcionario,
    Cliente,
    Fornecedor,
    Produto,
    Venda,
    VendaItem,
    MovimentacaoEstoque,
    Despesa,
)


DEFAULT_ESTABELECIMENTO_ID = 4


def _faker() -> Faker:
    fake = Faker("pt_BR")
    Faker.seed(20260102)
    return fake


def _safe_unique(fake: Faker, attr: str, fallback_fn):
    """Tenta usar provider de locale; se não existir, usa fallback."""
    if hasattr(fake, attr):
        return getattr(fake, attr)()
    return fallback_fn()


def reset_database():
    """Destrói e recria o esquema do banco (SQLite/Postgres)."""
    print("🧹 Iniciando RESET do banco de dados...")

    try:
        engine_name = db.engine.name
        print(f"  - Banco detectado: {engine_name}")

        # Estratégia Híbrida Inteligente
        if engine_name == "sqlite":
            # No SQLite local, é mais seguro apagar o arquivo ou fazer drop_all
            print("  - [SQLite] Recriando tabelas (DROP/CREATE)...")
            db.drop_all()
            db.create_all()
        else:
            # No Postgres (Render), TRUNCATE é mais eficiente e seguro para produção
            print("  - [Postgres] Limpando dados (TRUNCATE CASCADE)...")
            # Lista de tabelas ordenada para evitar erros de FK se o cascade falhar
            tabelas = [
                "movimentacoes_estoque",
                "venda_itens",
                "pagamentos",
                "vendas",
                "despesas",
                "contas_pagar",
                "contas_receber",
                "pedido_compra_itens",
                "pedidos_compra",
                "produtos",
                "fornecedores",
                "clientes",
                "login_history",
                "funcionarios",
                "configuracoes",
                "dashboard_metricas",
                "relatorios_agendados",
                "estabelecimentos",
                "alembic_version",
            ]
            for tabela in tabelas:
                try:
                    db.session.execute(
                        text(f"TRUNCATE TABLE {tabela} RESTART IDENTITY CASCADE")
                    )
                except Exception:
                    pass  # Ignora se tabela não existir

            # Garante que a estrutura esteja atualizada
            db.create_all()

        db.session.commit()
        print("✅ Banco limpo e estruturado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao resetar banco: {e}")
        db.session.rollback()


def ensure_estabelecimento(fake: Faker, estabelecimento_id: int) -> Estabelecimento:
    # Correção para SQLAlchemy 2.0+ (Session.get)
    est = db.session.get(Estabelecimento, estabelecimento_id)
    if est:
        return est

    # CORREÇÃO: Usar nome_fantasia e razao_social em vez de 'nome'
    nome_ficticio = f"Mercadinho {fake.city()}"
    est = Estabelecimento(
        id=estabelecimento_id,
        nome_fantasia=nome_ficticio,
        razao_social=f"{nome_ficticio} LTDA",
        cnpj=_safe_unique(
            fake,
            "cnpj",
            lambda: f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
        ),
        telefone=fake.phone_number(),
        email=fake.company_email(),
        cep=fake.postcode(),
        logradouro=fake.street_name(),
        numero=str(random.randint(1, 9999)),
        bairro=fake.bairro() if hasattr(fake, "bairro") else "Centro",
        cidade=fake.city(),
        estado=fake.estado_sigla() if hasattr(fake, "estado_sigla") else "SP",
        data_abertura=date.today() - timedelta(days=365 * 5),
        data_cadastro=datetime.now() - timedelta(days=365),
        ativo=True,
    )
    db.session.add(est)
    db.session.commit()
    return est


def ensure_configuracao(estabelecimento_id: int) -> Configuracao:
    cfg = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
    if cfg:
        return cfg

    # CORREÇÃO: Remover campos que não existem no model Configuracao atual
    cfg = Configuracao(
        estabelecimento_id=estabelecimento_id,
        cor_principal="#4F46E5",
        desconto_maximo_funcionario=10.00,
        controlar_validade=True,
        alerta_estoque_minimo=True,
        emitir_nfce=True,
    )
    db.session.add(cfg)
    db.session.commit()
    return cfg


def seed_funcionarios(fake: Faker, estabelecimento_id: int) -> List[Funcionario]:
    print("👥 Criando funcionários...")

    dados = [
        ("admin", "Administrador", "dono", "admin", "admin123"),
        ("gerente", fake.name(), "gerente", "gerente", "123456"),
        ("caixa1", fake.name(), "caixa", "funcionario", "123456"),
        ("caixa2", fake.name(), "caixa", "funcionario", "123456"),
    ]

    funcionarios: List[Funcionario] = []
    for username, nome, cargo, role, senha in dados:
        existente = Funcionario.query.filter_by(username=username).first()
        if existente:
            funcionarios.append(existente)
            continue

        f = Funcionario(
            estabelecimento_id=estabelecimento_id,
            nome=nome,
            username=username,
            cpf=_safe_unique(
                fake,
                "cpf",
                lambda: f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}",
            ),
            rg=str(random.randint(10000000, 99999999)),
            data_nascimento=date(1990, 1, 1),
            telefone=fake.phone_number(),
            email=fake.email(),
            cargo=cargo,
            role=role,
            # Campos de endereço obrigatórios
            cep=fake.postcode(),
            logradouro=fake.street_name(),
            numero=str(random.randint(1, 1000)),
            bairro="Centro",
            cidade=fake.city(),
            estado="SP",
            data_admissao=date.today() - timedelta(days=365),
            ativo=True,
            permissoes={
                "pdv": True,
                "estoque": True,
                "configuracoes": role == "admin",
            },
        )
        f.set_senha(senha)
        db.session.add(f)
        funcionarios.append(f)

    db.session.commit()
    return funcionarios


def seed_clientes(fake: Faker, estabelecimento_id: int, n: int = 40) -> List[Cliente]:
    print("🧑‍🤝‍🧑 Criando clientes...")
    clientes: List[Cliente] = []
    for _ in range(n):
        c = Cliente(
            estabelecimento_id=estabelecimento_id,
            nome=fake.name(),
            cpf=_safe_unique(fake, "cpf", lambda: fake.ssn()),
            celular=fake.phone_number(),
            email=fake.email(),
            # Campos de endereço obrigatórios do Mixin
            cep=fake.postcode(),
            logradouro=fake.street_address(),
            numero=str(random.randint(1, 500)),
            bairro="Centro",
            cidade=fake.city(),
            estado="SP",
            data_cadastro=datetime.now() - timedelta(days=random.randint(10, 365)),
            total_compras=0,
            ativo=True,
        )
        db.session.add(c)
        clientes.append(c)
    db.session.commit()
    return clientes


def seed_fornecedores(
    fake: Faker, estabelecimento_id: int, n: int = 6
) -> List[Fornecedor]:
    print("🏭 Criando fornecedores...")
    fornecedores: List[Fornecedor] = []
    for _ in range(n):
        nome_empresa = fake.company()
        forn = Fornecedor(
            estabelecimento_id=estabelecimento_id,
            # CORREÇÃO: Usar nome_fantasia e razao_social
            nome_fantasia=nome_empresa,
            razao_social=f"{nome_empresa} S.A",
            cnpj=_safe_unique(fake, "cnpj", lambda: fake.ssn()),
            telefone=fake.phone_number(),
            email=fake.company_email(),
            # Campos de endereço obrigatórios
            cep=fake.postcode(),
            logradouro=fake.street_address(),
            numero=str(random.randint(1, 2000)),
            bairro="Industrial",
            cidade=fake.city(),
            estado="SP",
            contato_nome=fake.name(),
            ativo=True,
            prazo_entrega=random.randint(1, 10),
            forma_pagamento=random.choice(["à vista", "15 dias", "30 dias", "45 dias"]),
        )
        db.session.add(forn)
        fornecedores.append(forn)
    db.session.commit()
    return fornecedores


def seed_produtos(
    fake: Faker,
    estabelecimento_id: int,
    fornecedores: List[Fornecedor],
    n: int = 120,
) -> List[Produto]:
    print("📦 Criando produtos realistas...")

    produtos_reais = {
        "Bebidas": [
            ("Coca-Cola 2L", "Coca-Cola", 8.50, 10.99, "UN"),
            ("Guaraná Antarctica 2L", "Ambev", 7.80, 9.99, "UN"),
            ("Cerveja Skol 350ml", "Ambev", 2.50, 3.99, "UN"),
        ],
        "Mercearia": [
            ("Arroz Tio João 5kg", "Tio João", 22.00, 29.90, "UN"),
            ("Feijão Camil 1kg", "Camil", 6.50, 8.99, "UN"),
            ("Macarrão Galo 500g", "Galo", 3.50, 5.90, "UN"),
        ],
        "Higiene": [
            ("Sabonete Dove", "Dove", 2.50, 4.50, "UN"),
            ("Papel Higiênico Neve", "Neve", 12.00, 18.90, "UN"),
        ],
    }

    produtos: List[Produto] = []
    hoje = date.today()

    # Criar produtos baseados na lista real
    for categoria, items in produtos_reais.items():
        for nome_prod, marca, custo, venda, unidade in items:
            p = Produto(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=random.choice(fornecedores).id,
                codigo_barras=fake.unique.ean13(),
                nome=nome_prod,
                descricao=f"{nome_prod} - {marca}",
                marca=marca,
                categoria=categoria,
                unidade_medida=unidade,
                quantidade=random.randint(10, 100),
                quantidade_minima=10,
                preco_custo=custo,
                preco_venda=venda,
                margem_lucro=round(((venda - custo) / custo) * 100, 2),
                data_validade=hoje + timedelta(days=random.randint(30, 365)),
                lote=f"L{random.randint(1000,9999)}",
                ativo=True,
            )
            db.session.add(p)
            produtos.append(p)

    # Preencher o restante com genéricos se necessário
    while len(produtos) < n:
        cat = random.choice(list(produtos_reais.keys()))
        custo = round(random.uniform(5.0, 50.0), 2)
        venda = round(custo * 1.4, 2)

        p = Produto(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=random.choice(fornecedores).id,
            codigo_barras=fake.unique.ean13(),
            nome=f"Produto Genérico {len(produtos)}",
            categoria=cat,
            unidade_medida="UN",
            quantidade=50,
            preco_custo=custo,
            preco_venda=venda,
            ativo=True,
        )
        db.session.add(p)
        produtos.append(p)

    db.session.commit()
    print(f"✓ {len(produtos)} produtos criados")
    return produtos


def _pick_sale_datetime(base_day: date) -> datetime:
    hour_bucket = random.choices(
        population=[9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        weights=[2, 6, 7, 6, 3, 3, 3, 4, 7, 8, 6, 2],
        k=1,
    )[0]
    return datetime.combine(base_day, datetime.min.time()).replace(
        hour=hour_bucket, minute=random.randint(0, 59), second=random.randint(0, 59)
    )


def seed_vendas(
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    clientes: List[Cliente],
    produtos: List[Produto],
    dias: int = 30,
    vendas_dia: float = 4.0,
    vendas_hoje: int = 10,
):
    print("🧾 Criando vendas e itens...")
    hoje = date.today()
    vendas_criadas = 0

    # Função auxiliar para criar uma venda
    def criar_venda(data_venda, seq):
        funcionario = random.choice(funcionarios)
        cliente = random.choice([None] + clientes)

        # CORREÇÃO: Remover 'tipo_venda' se não existe no model
        # Assumindo que Venda tem campos básicos
        venda = Venda(
            estabelecimento_id=estabelecimento_id,
            cliente_id=cliente.id if cliente else None,
            funcionario_id=funcionario.id,
            codigo=f"V{data_venda.strftime('%Y%m%d')}{seq:04d}",
            forma_pagamento=random.choice(["dinheiro", "pix", "cartao"]),
            status="finalizada",
            data_venda=data_venda,
            quantidade_itens=0,
            subtotal=0,
            desconto=0,
            total=0,
            valor_recebido=0,
            troco=0,
        )
        db.session.add(venda)
        db.session.flush()

        total = 0
        qtd_total = 0

        # Adicionar itens
        for _ in range(random.randint(1, 5)):
            prod = random.choice(produtos)
            qtd = random.randint(1, 3)
            preco = float(prod.preco_venda)

            item = VendaItem(
                venda_id=venda.id,
                produto_id=prod.id,
                produto_nome=prod.nome,
                quantidade=qtd,
                preco_unitario=preco,
                total_item=preco * qtd,
            )
            db.session.add(item)

            # Movimentação de estoque
            mov = MovimentacaoEstoque(
                estabelecimento_id=estabelecimento_id,
                produto_id=prod.id,
                venda_id=venda.id,
                funcionario_id=funcionario.id,
                tipo="saida",
                quantidade=qtd,
                quantidade_anterior=prod.quantidade,
                quantidade_atual=prod.quantidade - qtd,
                motivo="Venda",
                created_at=data_venda,
            )
            db.session.add(mov)

            # Baixa no estoque
            prod.quantidade -= qtd
            prod.total_vendido = float(prod.total_vendido or 0) + (preco * qtd)

            total += preco * qtd
            qtd_total += qtd

        venda.subtotal = total
        venda.total = total
        venda.quantidade_itens = qtd_total
        venda.valor_recebido = total

        if cliente:
            cliente.total_compras += 1

        return venda

    # Loop para vendas passadas
    for d in range(dias, 0, -1):
        dia = hoje - timedelta(days=d)
        n = max(1, int(random.gauss(vendas_dia, 1)))
        for i in range(n):
            vendas_criadas += 1
            criar_venda(_pick_sale_datetime(dia), vendas_criadas)

    # Loop para vendas hoje
    for i in range(vendas_hoje):
        vendas_criadas += 1
        criar_venda(_pick_sale_datetime(hoje), vendas_criadas)

    db.session.commit()
    print(f"✓ {vendas_criadas} vendas criadas.")


def seed_despesas(fake: Faker, estabelecimento_id: int):
    print("💸 Criando despesas...")
    d = Despesa(
        estabelecimento_id=estabelecimento_id,
        descricao="Aluguel",
        categoria="Aluguel",
        tipo="fixa",
        valor=2500.0,
        data_despesa=date.today(),
        forma_pagamento="pix",
        recorrente=True,
    )
    db.session.add(d)
    db.session.commit()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Seed de dados de teste")
    parser.add_argument("--reset", action="store_true", help="Apaga e recria os dados")
    parser.add_argument(
        "--estabelecimento-id", type=int, default=DEFAULT_ESTABELECIMENTO_ID
    )
    parser.add_argument("--clientes", type=int, default=40)
    parser.add_argument("--fornecedores", type=int, default=6)
    parser.add_argument("--produtos", type=int, default=120)
    parser.add_argument("--dias", type=int, default=180)
    parser.add_argument("--vendas-dia", type=float, default=4.0)
    parser.add_argument("--vendas-hoje", type=int, default=20)
    args = parser.parse_args(argv)

    fake = _faker()

    app = create_app(os.getenv("FLASK_ENV", "default"))
    with app.app_context():

        # --- BLINDAGEM CONTRA ERROS ---
        # 1. Tenta criar todas as tabelas se não existirem
        print("🔍 Verificando estrutura do banco...")
        try:
            db.create_all()
        except Exception as e:
            print(f"⚠️ Erro no create_all (pode ser ignorado se tabelas existem): {e}")

        # 2. Reseta se solicitado OU se a tabela estiver vazia
        deve_resetar = args.reset
        if not deve_resetar:
            # Verifica se tem dados usando a nova sintaxe do SQLAlchemy 2.0
            est_existente = db.session.get(Estabelecimento, args.estabelecimento_id)
            if not est_existente:
                print("⚠️ Banco vazio detectado. Forçando RESET...")
                deve_resetar = True
            else:
                print("⚠️ Já existem dados. Use --reset para apagar.")
                return 0

        if deve_resetar:
            reset_database()

        # 3. Popula os dados
        try:
            est = ensure_estabelecimento(fake, args.estabelecimento_id)
            ensure_configuracao(est.id)

            funcionarios = seed_funcionarios(fake, est.id)
            clientes = seed_clientes(fake, est.id, n=args.clientes)
            fornecedores = seed_fornecedores(fake, est.id, n=args.fornecedores)
            produtos = seed_produtos(fake, est.id, fornecedores, n=args.produtos)
            seed_vendas(
                est.id,
                funcionarios,
                clientes,
                produtos,
                dias=args.dias,
                vendas_dia=args.vendas_dia,
                vendas_hoje=args.vendas_hoje,
            )
            seed_despesas(fake, est.id)

            print("\n" + "=" * 60)
            print("✅ SEED CONCLUÍDO COM SUCESSO!")
            print("=" * 60)
            print(f"Estabelecimento: {est.nome_fantasia}")
            print("Login Admin: admin / admin123")
            print("=" * 60)

        except Exception as e:
            print(f"❌ ERRO CRÍTICO NO SEED: {e}")
            import traceback

            traceback.print_exc()
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
