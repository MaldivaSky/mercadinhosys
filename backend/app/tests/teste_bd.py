"""Script de inspeção do banco para validar dados do seed.

Uso (Windows / PowerShell):
  C:/Users/rafae/OneDrive/Desktop/mercadinhosys/backend/venv/Scripts/python.exe \
    C:/Users/rafae/OneDrive/Desktop/mercadinhosys/backend/app/tests/teste_bd.py \
    --estabelecimento-id 4 --limit 10

Observação:
- Não precisa subir o servidor.
- Apenas lê o banco e imprime um resumo + amostras.
"""

from __future__ import annotations

import os
import sys
import argparse
from datetime import datetime, date, timedelta

from sqlalchemy import func

# Garante imports do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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


def _fmt_money(v: float) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _print_header(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspeciona dados criados pelo seed")
    parser.add_argument("--estabelecimento-id", type=int, default=4)
    parser.add_argument("--limit", type=int, default=10, help="Quantidade de linhas de exemplo")
    args = parser.parse_args(argv)

    app = create_app(os.getenv("FLASK_ENV", "default"))

    with app.app_context():
        est = Estabelecimento.query.get(args.estabelecimento_id)
        if not est:
            print(f"❌ Estabelecimento {args.estabelecimento_id} não encontrado")
            print("Dica: rode o seed: backend/seed_test.py --reset")
            return 1

        _print_header("🏪 ESTABELECIMENTO")
        print(f"ID: {est.id}")
        print(f"Nome: {est.nome}")
        print(f"Cidade/UF: {est.cidade}/{est.estado}")

        cfg = Configuracao.query.filter_by(estabelecimento_id=est.id).first()
        print(f"Configuração: {'OK' if cfg else 'NÃO ENCONTRADA'}")
        if cfg:
            print(f"Meta diária: {_fmt_money(cfg.meta_vendas_diaria)}")
            print(f"Meta mensal: {_fmt_money(cfg.meta_vendas_mensal)}")
            print(f"Dias alerta validade: {cfg.dias_alerta_validade}")

        _print_header("📊 CONTAGENS")
        counts = {
            "funcionarios": Funcionario.query.filter_by(estabelecimento_id=est.id).count(),
            "clientes": Cliente.query.filter_by(estabelecimento_id=est.id).count(),
            "fornecedores": Fornecedor.query.filter_by(estabelecimento_id=est.id).count(),
            "produtos": Produto.query.filter_by(estabelecimento_id=est.id).count(),
            "vendas": Venda.query.filter_by(estabelecimento_id=est.id).count(),
            "itens_venda": (
                db.session.query(func.count(VendaItem.id))
                .join(Venda, VendaItem.venda_id == Venda.id)
                .filter(Venda.estabelecimento_id == est.id)
                .scalar()
                or 0
            ),
            "mov_estoque": MovimentacaoEstoque.query.filter_by(estabelecimento_id=est.id).count(),
            "despesas": Despesa.query.filter_by(estabelecimento_id=est.id).count(),
        }

        for k, v in counts.items():
            print(f"- {k}: {v}")

        _print_header("🧾 VENDAS (AMOSTRA)")
        vendas = (
            Venda.query.filter_by(estabelecimento_id=est.id)
            .order_by(Venda.data_venda.desc())
            .limit(args.limit)
            .all()
        )

        if not vendas:
            print("(sem vendas)")
        else:
            for v in vendas:
                print(
                    f"#{v.id} | {v.data_venda.strftime('%Y-%m-%d %H:%M:%S') if v.data_venda else None} | "
                    f"total={_fmt_money(v.total)} | status={v.status} | fp={v.forma_pagamento} | itens={v.quantidade_itens}"
                )

        # Intervalo de datas e agregados do mês
        _print_header("📈 AGREGADOS (HOJE / MÊS)")
        hoje = date.today()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())
        inicio_mes = datetime(hoje.year, hoje.month, 1)

        total_hoje = (
            db.session.query(func.sum(Venda.total))
            .filter(
                Venda.estabelecimento_id == est.id,
                Venda.data_venda >= inicio_dia,
                Venda.data_venda <= fim_dia,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        qtd_hoje = (
            db.session.query(func.count(Venda.id))
            .filter(
                Venda.estabelecimento_id == est.id,
                Venda.data_venda >= inicio_dia,
                Venda.data_venda <= fim_dia,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        total_mes = (
            db.session.query(func.sum(Venda.total))
            .filter(
                Venda.estabelecimento_id == est.id,
                Venda.data_venda >= inicio_mes,
                Venda.data_venda <= fim_dia,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        despesas_mes = (
            db.session.query(func.sum(Despesa.valor))
            .filter(
                Despesa.estabelecimento_id == est.id,
                Despesa.data_despesa >= inicio_mes.date(),
                Despesa.data_despesa <= hoje,
            )
            .scalar()
            or 0
        )

        print(f"Vendas hoje: {qtd_hoje} | Total hoje: {_fmt_money(total_hoje)}")
        print(f"Total mês: {_fmt_money(total_mes)}")
        print(f"Despesas mês: {_fmt_money(despesas_mes)}")
        print(f"Lucro bruto mês (aprox): {_fmt_money(total_mes - despesas_mes)}")

        _print_header("💸 DESPESAS (AMOSTRA)")
        despesas = (
            Despesa.query.filter_by(estabelecimento_id=est.id)
            .order_by(Despesa.data_despesa.desc(), Despesa.id.desc())
            .limit(args.limit)
            .all()
        )
        if not despesas:
            print("(sem despesas)")
        else:
            for d in despesas:
                print(
                    f"#{d.id} | {d.data_despesa} | {_fmt_money(d.valor)} | {d.categoria} | {d.tipo} | {d.descricao}"
                )

        _print_header("📦 PRODUTOS (ALERTAS)")
        baixo_estoque = (
            Produto.query.filter(
                Produto.estabelecimento_id == est.id,
                Produto.ativo == True,
                Produto.quantidade > 0,
                Produto.quantidade < Produto.quantidade_minima,
            )
            .count()
        )
        esgotados = (
            Produto.query.filter(
                Produto.estabelecimento_id == est.id,
                Produto.ativo == True,
                Produto.quantidade <= 0,
            )
            .count()
        )

        vencidos = (
            Produto.query.filter(
                Produto.estabelecimento_id == est.id,
                Produto.data_validade.isnot(None),
                Produto.data_validade < hoje,
                Produto.quantidade > 0,
            )
            .count()
        )

        dias_alerta = cfg.dias_alerta_validade if cfg else 15
        limite_validade = hoje + timedelta(days=dias_alerta)
        validade_proxima = (
            Produto.query.filter(
                Produto.estabelecimento_id == est.id,
                Produto.data_validade.isnot(None),
                Produto.data_validade >= hoje,
                Produto.data_validade <= limite_validade,
                Produto.quantidade > 0,
            )
            .count()
        )

        print(f"Baixo estoque: {baixo_estoque}")
        print(f"Esgotados: {esgotados}")
        print(f"Vencidos (com quantidade): {vencidos}")
        print(f"Validade próxima (<= {dias_alerta} dias): {validade_proxima}")

        # Amostra de produtos críticos
        criticos = (
            Produto.query.filter(
                Produto.estabelecimento_id == est.id,
                Produto.ativo == True,
                ((Produto.quantidade <= 0) | (Produto.quantidade < Produto.quantidade_minima)),
            )
            .order_by(Produto.quantidade.asc())
            .limit(args.limit)
            .all()
        )

        if criticos:
            print("\nAmostra produtos críticos:")
            for p in criticos:
                print(
                    f"#{p.id} | {p.nome} | qtd={p.quantidade} | min={p.quantidade_minima} | validade={p.data_validade}"
                )

        print("\n✅ Inspeção concluída.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
