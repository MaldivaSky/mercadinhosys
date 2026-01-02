"""Seed de dados fictícios para testes (dashboard + relatórios + despesas).

Objetivos:
- Gerar dados realistas e suficientes para alimentar:
  - dashboard avançado (tendências, sazonalidade, hora pico, top produtos)
  - relatórios (vendas/estoque/clientes/financeiro)
  - módulo de despesas

Uso:
  - `C:/.../python.exe backend/seed_test.py --reset`

Padrões importantes do projeto:
- Muitos testes e exemplos usam `estabelecimento_id=4`.
- O dashboard calcula métricas com base em vendas do dia e do mês.
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
    """Limpa tabelas principais (modo teste)."""
    print("🧹 Limpando dados existentes...")

    # Ordem inversa de dependência (FK)
    tabelas = [
        "movimentacoes_estoque",
        "venda_itens",
        "vendas",
        "despesas",
        "produtos",
        "fornecedores",
        "clientes",
        "login_history",
        "funcionarios",
        "configuracoes",
        "dashboard_metricas",
        "relatorios_agendados",
        "estabelecimentos",
    ]

    db.session.execute(text("PRAGMA foreign_keys = OFF"))
    for tabela in tabelas:
        try:
            db.session.execute(text(f"DELETE FROM {tabela}"))
            print(f"  - Limpou {tabela}")
        except Exception as e:
            print(f"  - Ignorando {tabela}: {e}")
    db.session.execute(text("PRAGMA foreign_keys = ON"))
    db.session.commit()


def ensure_estabelecimento(fake: Faker, estabelecimento_id: int) -> Estabelecimento:
    est = Estabelecimento.query.get(estabelecimento_id)
    if est:
        return est

    est = Estabelecimento(
        id=estabelecimento_id,
        nome=f"Mercadinho {fake.city()}",
        cnpj=_safe_unique(fake, "cnpj", lambda: f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}"),
        telefone=fake.phone_number(),
        email=fake.company_email(),
        cep=fake.postcode(),
        endereco=fake.street_address(),
        cidade=fake.city(),
        estado=fake.estado_sigla() if hasattr(fake, "estado_sigla") else "SP",
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

    cfg = Configuracao(
        estabelecimento_id=estabelecimento_id,
        cor_principal="#4F46E5",
        dias_alerta_validade=15,
        estoque_minimo_padrao=10,
        meta_vendas_diaria=1200.0,
        meta_vendas_mensal=35000.0,
        dashboard_analytics_avancado=True,
        formas_pagamento={
            "dinheiro": {"ativo": True, "taxa": 0, "exige_troco": True},
            "cartao_credito": {"ativo": True, "taxa": 2.5, "parcelas": 12},
            "cartao_debito": {"ativo": True, "taxa": 1.5},
            "pix": {"ativo": True, "taxa": 0},
        },
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
            cpf=_safe_unique(fake, "cpf", lambda: f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"),
            telefone=fake.phone_number(),
            email=fake.email(),
            cargo=cargo,
            role=role,
            status="ativo",
            data_admissao=date.today() - timedelta(days=365),
            ativo=True,
            permissoes={
                "acesso_pdv": True,
                "acesso_estoque": True,
                "acesso_relatorios": True,
                "acesso_configuracoes": role == "admin",
                "acesso_financeiro": role in ["admin", "gerente"],
                "pode_dar_desconto": True,
                "limite_desconto": 10.0,
                "pode_cancelar_venda": role in ["admin", "gerente"],
                "acesso_dashboard_avancado": role in ["admin", "gerente"],
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
            cpf_cnpj=_safe_unique(fake, "cpf", lambda: fake.ssn()),
            telefone=fake.phone_number(),
            email=fake.email(),
            endereco=fake.address(),
            data_cadastro=datetime.now() - timedelta(days=random.randint(10, 365)),
            total_compras=0.0,
            frequencia_compras=0,
            valor_medio_compra=0.0,
            dias_ultima_compra=0,
            segmento_rfm="novo",
        )
        db.session.add(c)
        clientes.append(c)
    db.session.commit()
    return clientes


def seed_fornecedores(fake: Faker, estabelecimento_id: int, n: int = 6) -> List[Fornecedor]:
    print("🏭 Criando fornecedores...")
    fornecedores: List[Fornecedor] = []
    for _ in range(n):
        forn = Fornecedor(
            estabelecimento_id=estabelecimento_id,
            nome=fake.company(),
            cnpj=_safe_unique(fake, "cnpj", lambda: fake.ssn()),
            telefone=fake.phone_number(),
            email=fake.company_email(),
            endereco=fake.street_address(),
            cidade=fake.city(),
            estado=fake.estado_sigla() if hasattr(fake, "estado_sigla") else "SP",
            contato_comercial=fake.name(),
            contato_nome=fake.name(),
            celular_comercial=fake.phone_number(),
            ativo=True,
            prazo_entrega=random.randint(1, 10),
            forma_pagamento=random.choice(["à vista", "15 dias", "30 dias", "45 dias"]),
            avaliacao=round(random.uniform(3.5, 5.0), 1),
            tempo_medio_entrega=random.randint(1, 7),
            taxa_atendimento=round(random.uniform(90.0, 100.0), 1),
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
    print("📦 Criando produtos...")
    categorias = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Padaria", "Açougue"]
    marcas = ["BomPreço", "Qualitá", "TopMix", "Vida", "Sabor+", "Eco"]
    unidades = ["UN", "KG", "LT"]
    produtos: List[Produto] = []

    hoje = date.today()
    for i in range(n):
        preco_custo = round(random.uniform(0.8, 40.0), 2)
        margem = random.uniform(1.25, 2.2)
        preco_venda = round(preco_custo * margem, 2)

        # Valididade: mistura entre vencidos, próximos e ok
        if i < max(3, n // 20):
            data_validade = hoje - timedelta(days=random.randint(1, 15))
        elif i < max(10, n // 10):
            data_validade = hoje + timedelta(days=random.randint(1, 10))
        else:
            data_validade = hoje + timedelta(days=random.randint(20, 365))

        # Estoque: garante alguns esgotados e alguns baixos
        if i < max(5, n // 24):
            quantidade = 0
        elif i < max(15, n // 8):
            quantidade = random.randint(1, 5)
        else:
            quantidade = random.randint(10, 200)

        quantidade_minima = random.choice([5, 8, 10, 12, 15])

        p = Produto(
            estabelecimento_id=estabelecimento_id,
            fornecedor_id=random.choice(fornecedores).id,
            codigo_barras=fake.unique.ean13(),
            nome=f"{random.choice(categorias)} - {fake.word().capitalize()} {i+1}",
            descricao=fake.sentence(nb_words=10),
            marca=random.choice(marcas),
            fabricante=random.choice(marcas),
            categoria=random.choice(categorias),
            subcategoria=fake.word().capitalize(),
            unidade_medida=random.choice(unidades),
            quantidade=quantidade,
            quantidade_minima=quantidade_minima,
            localizacao=f"Corredor {random.randint(1, 10)}",
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            margem_lucro=round(((preco_venda - preco_custo) / preco_custo) * 100, 2),
            data_validade=data_validade,
            lote=f"L{random.randint(1000,9999)}",
            ativo=True,
        )
        db.session.add(p)
        produtos.append(p)

    db.session.commit()
    return produtos


def _pick_sale_datetime(base_day: date) -> datetime:
    """Cria horários com pico realista (manhã/tarde/noite)."""
    # Distribuição aproximada: pico 10-12 e 17-19
    hour_bucket = random.choices(
        population=[9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        weights=[2, 6, 7, 6, 3, 3, 3, 4, 7, 8, 6, 2],
        k=1,
    )[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime.combine(base_day, datetime.min.time()).replace(
        hour=hour_bucket, minute=minute, second=second
    )


def seed_vendas(
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    clientes: List[Cliente],
    produtos: List[Produto],
    dias: int = 180,
    vendas_por_dia_media: float = 4.0,
    vendas_hoje: int = 20,
):
    print("🧾 Criando vendas e itens...")

    formas_pagamento = ["dinheiro", "cartao_credito", "cartao_debito", "pix"]
    hoje = date.today()

    vendas_criadas = 0
    # Dias anteriores
    for d in range(dias, 0, -1):
        dia = hoje - timedelta(days=d)
        n_vendas = max(0, int(random.gauss(vendas_por_dia_media, 1.5)))
        for i in range(n_vendas):
            data_venda = _pick_sale_datetime(dia)
            vendas_criadas += 1
            _criar_venda_com_itens(
                estabelecimento_id,
                funcionarios,
                clientes,
                produtos,
                formas_pagamento,
                data_venda,
                seq=vendas_criadas,
            )

    # Hoje (garante dados pro dashboard)
    for i in range(vendas_hoje):
        data_venda = _pick_sale_datetime(hoje)
        vendas_criadas += 1
        _criar_venda_com_itens(
            estabelecimento_id,
            funcionarios,
            clientes,
            produtos,
            formas_pagamento,
            data_venda,
            seq=vendas_criadas,
        )

    db.session.commit()
    print(f"✓ Vendas criadas: {vendas_criadas}")


def _criar_venda_com_itens(
    estabelecimento_id: int,
    funcionarios: List[Funcionario],
    clientes: List[Cliente],
    produtos: List[Produto],
    formas_pagamento: List[str],
    data_venda: datetime,
    seq: int,
):
    funcionario = random.choice(funcionarios)
    cliente = random.choice([None] + clientes)

    codigo = f"V{data_venda.strftime('%Y%m%d%H%M%S')}{seq:06d}"
    venda = Venda(
        estabelecimento_id=estabelecimento_id,
        cliente_id=cliente.id if cliente else None,
        funcionario_id=funcionario.id,
        codigo=codigo,
        subtotal=0.0,
        desconto=0.0,
        total=0.0,
        forma_pagamento=random.choice(formas_pagamento),
        valor_recebido=0.0,
        troco=0.0,
        status="finalizada",
        data_venda=data_venda,
        created_at=data_venda,
        updated_at=data_venda,
        quantidade_itens=0,
        tipo_venda=random.choice(["normal", "normal", "normal", "promocional", "atacado"]),
    )
    db.session.add(venda)
    db.session.flush()  # garante venda.id

    total_venda = 0.0
    total_itens = 0

    # 1..8 itens
    for _ in range(random.randint(1, 8)):
        produto = random.choice(produtos)
        quantidade = random.randint(1, 5)

        preco_unitario = float(produto.preco_venda)
        custo_unitario = float(produto.preco_custo)
        desconto_item = 0.0
        if venda.tipo_venda in ["promocional"] and random.random() < 0.25:
            desconto_item = round(preco_unitario * random.uniform(0.05, 0.15), 2)

        total_item = round((preco_unitario - desconto_item) * quantidade, 2)
        margem_item = (
            round(((preco_unitario - custo_unitario) / custo_unitario) * 100, 2)
            if custo_unitario > 0
            else 0.0
        )

        item = VendaItem(
            venda_id=venda.id,
            produto_id=produto.id,
            produto_nome=produto.nome,
            descricao=produto.descricao,
            produto_codigo=produto.codigo_barras,
            produto_unidade=produto.unidade_medida,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            desconto=desconto_item,
            total_item=total_item,
            custo_unitario=custo_unitario,
            margem_item=margem_item,
            created_at=data_venda,
        )
        db.session.add(item)

        # Atualizar estoque
        quantidade_anterior = int(produto.quantidade or 0)
        produto.quantidade = max(0, quantidade_anterior - quantidade)

        mov = MovimentacaoEstoque(
            estabelecimento_id=estabelecimento_id,
            produto_id=produto.id,
            venda_id=venda.id,
            funcionario_id=funcionario.id,
            tipo="saida",
            quantidade=quantidade,
            quantidade_anterior=quantidade_anterior,
            quantidade_atual=int(produto.quantidade),
            custo_unitario=custo_unitario,
            valor_total=round(custo_unitario * quantidade, 2),
            motivo="Venda",
            created_at=data_venda,
        )
        db.session.add(mov)

        # Métricas produto
        produto.total_vendido = float(produto.total_vendido or 0) + float(total_item)
        produto.quantidade_vendida = int(produto.quantidade_vendida or 0) + quantidade
        produto.frequencia_venda = int(produto.frequencia_venda or 0) + 1
        produto.ultima_venda = data_venda

        total_venda += total_item
        total_itens += quantidade

    venda.subtotal = round(total_venda, 2)
    venda.total = round(total_venda, 2)
    venda.quantidade_itens = int(total_itens)
    venda.valor_recebido = venda.total

    if venda.forma_pagamento == "dinheiro":
        recebido = round((venda.total + 4.99) / 5) * 5
        venda.valor_recebido = float(recebido)
        venda.troco = round(float(recebido) - float(venda.total), 2)

    # Atualiza cliente (se houver)
    if cliente:
        cliente.total_compras = float(cliente.total_compras or 0) + float(venda.total)
        cliente.frequencia_compras = int(cliente.frequencia_compras or 0) + 1
        cliente.ultima_compra = data_venda


def seed_despesas(fake: Faker, estabelecimento_id: int):
    print("💸 Criando despesas (mês atual)...")
    hoje = date.today()
    inicio_mes = date(hoje.year, hoje.month, 1)

    categorias_fixas = [
        ("Aluguel", "fixa", 2500.0, True),
        ("Internet", "fixa", 180.0, True),
        ("Energia", "fixa", 900.0, True),
    ]

    # Fixas (1x no mês)
    for nome, tipo, valor, recorrente in categorias_fixas:
        d = Despesa(
            estabelecimento_id=estabelecimento_id,
            descricao=nome,
            categoria=nome,
            tipo=tipo,
            valor=float(valor),
            data_despesa=inicio_mes,
            forma_pagamento=random.choice(["pix", "boleto", "dinheiro"]),
            recorrente=recorrente,
            observacoes=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.session.add(d)

    # Variáveis (diárias)
    dias_no_mes = (hoje - inicio_mes).days + 1
    for i in range(dias_no_mes):
        dia = inicio_mes + timedelta(days=i)
        # Nem todo dia tem despesa
        if random.random() < 0.55:
            continue

        descricao = random.choice(
            [
                "Compra de insumos",
                "Manutenção",
                "Frete",
                "Material de limpeza",
                "Pequenos reparos",
            ]
        )
        categoria = random.choice(["Operacional", "Insumos", "Manutenção", "Frete"])
        valor = round(random.uniform(30.0, 450.0), 2)
        d = Despesa(
            estabelecimento_id=estabelecimento_id,
            descricao=descricao,
            categoria=categoria,
            tipo="variavel",
            valor=float(valor),
            data_despesa=dia,
            forma_pagamento=random.choice(["pix", "dinheiro", "cartao_debito"]),
            recorrente=False,
            observacoes=fake.sentence(nb_words=6),
            created_at=datetime.combine(dia, datetime.min.time()) + timedelta(hours=9),
            updated_at=datetime.combine(dia, datetime.min.time()) + timedelta(hours=9),
        )
        db.session.add(d)

    db.session.commit()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Seed de dados de teste")
    parser.add_argument("--reset", action="store_true", help="Apaga e recria os dados")
    parser.add_argument(
        "--estabelecimento-id",
        type=int,
        default=DEFAULT_ESTABELECIMENTO_ID,
        help="ID do estabelecimento principal (padrão: 4)",
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
        if args.reset:
            reset_database()
        else:
            # Se já tem dados, evita duplicar sem querer
            if Estabelecimento.query.first():
                print(
                    "⚠️ Já existem dados no banco. Use `--reset` para limpar e recriar."
                )
                return 1

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
            vendas_por_dia_media=args.vendas_dia,
            vendas_hoje=args.vendas_hoje,
        )
        seed_despesas(fake, est.id)

        print("\n" + "=" * 60)
        print("✅ SEED CONCLUÍDO")
        print("=" * 60)
        print(f"Estabelecimento principal: {est.id} ({est.nome})")
        print("Credenciais:")
        print("  - admin / admin123 (role: admin)")
        print("  - gerente / 123456 (role: gerente)")
        print("  - caixa1 / 123456 (role: funcionario)")
        print("  - caixa2 / 123456 (role: funcionario)")
        print("Dica relatórios: use `?estabelecimento_id=4` nas rotas de relatório.")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
