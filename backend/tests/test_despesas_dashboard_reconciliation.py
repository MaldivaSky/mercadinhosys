"""
Auditoria 2026-07-18 (WP1): o dashboard científico somava Despesa BRUTA —
categorias-espelho (fornecedores/folha de pagamento/benefícios/boleto de
mercadoria) contavam junto do CMV e a folha real (com encargos) nunca era
somada, fazendo Dashboard != página Despesas != DRE para o mesmo período.

Estes testes provam que DataLayer.get_total_expenses_value,
get_expense_details e get_sales_timeseries agora excluem os espelhos e somam
a folha REAL calculada (calcular_custo_folha_detalhado) uma única vez.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import db, Estabelecimento, Despesa
from app.dashboard_cientifico.data_layer import DataLayer
from app.services.rh_calculator_service import calcular_custo_folha_detalhado


def _add_despesa(estab_id, categoria, valor, dias_atras=5):
    d = (datetime.now(timezone.utc) - timedelta(days=dias_atras)).date()
    db.session.add(Despesa(
        estabelecimento_id=estab_id, descricao=f"Despesa {categoria}",
        categoria=categoria, tipo="variavel", valor=Decimal(str(valor)),
        data_despesa=d,
    ))


def test_total_expenses_exclui_espelhos_e_soma_folha_real(app, session):
    with app.app_context():
        estab = session.query(Estabelecimento).first()

        _add_despesa(estab.id, "geral", "300.00")
        _add_despesa(estab.id, "fornecedores", "5000.00")
        _add_despesa(estab.id, "folha de pagamento", "5000.00")
        _add_despesa(estab.id, "Benefícios", "200.00")
        _add_despesa(estab.id, "boleto de mercadoria", "1200.00")
        session.commit()

        start = datetime.now(timezone.utc) - timedelta(days=30)
        end = datetime.now(timezone.utc)

        folha = calcular_custo_folha_detalhado(estab.id, start.date(), end.date())
        custo_folha_real = float(folha["custo_folha"]["custo_real_total"])
        assert custo_folha_real > 0, "fixture tem funcionário ativo — folha real não pode ser zero"

        total = DataLayer.get_total_expenses_value(estab.id, start, end)

        # Só a despesa "geral" (não-espelho) + a folha REAL entram no total —
        # os R$5000+5000+200+1200 dos espelhos ficam de fora.
        esperado = 300.00 + custo_folha_real
        assert total == pytest.approx(esperado, abs=0.01)


def test_expense_details_soma_bate_com_total(app, session):
    with app.app_context():
        estab = session.query(Estabelecimento).first()
        _add_despesa(estab.id, "geral", "300.00")
        _add_despesa(estab.id, "fornecedores", "5000.00")
        session.commit()

        start = datetime.now(timezone.utc) - timedelta(days=30)
        end = datetime.now(timezone.utc)

        folha = calcular_custo_folha_detalhado(estab.id, start.date(), end.date())
        custo_folha_real = float(folha["custo_folha"]["custo_real_total"])

        total = DataLayer.get_total_expenses_value(estab.id, start, end)
        detalhes = DataLayer.get_expense_details(estab.id, start, end)
        soma_detalhes = sum(d["valor"] for d in detalhes)

        assert soma_detalhes == pytest.approx(total, abs=0.01)
        # A folha real aparece como linha própria, nunca some.
        assert any(d["tipo"] == "folha_calculada" for d in detalhes)
        # Só "geral" (não-espelho) + a folha real entram — o espelho de
        # R$5000 (fornecedores) não pode vazar na soma.
        assert soma_detalhes == pytest.approx(300.00 + custo_folha_real, abs=0.01)


def test_sales_timeseries_exclui_espelho_e_rateia_folha_real(app, session):
    with app.app_context():
        estab = session.query(Estabelecimento).first()
        dias_atras_folha = 3
        _add_despesa(estab.id, "folha de pagamento", "5000.00", dias_atras=dias_atras_folha)
        session.commit()

        days = 30
        serie = DataLayer.get_sales_timeseries(estab.id, days)
        assert len(serie) == days

        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).date()
        end_date = start_date + timedelta(days=days - 1)
        folha = calcular_custo_folha_detalhado(estab.id, start_date, end_date)
        custo_folha_dia_esperado = float(folha["custo_folha"]["custo_real_total"]) / days

        dia_da_despesa_mirror = (datetime.now(timezone.utc) - timedelta(days=dias_atras_folha)).strftime('%Y-%m-%d')
        entrada = next(d for d in serie if d["data"] == dia_da_despesa_mirror)

        # O espelho de R$5000 não pode aparecer inteiro num único dia — só o
        # rateio diário da folha REAL calculada.
        assert entrada["despesas"] < 1000, f"espelho de folha vazou no dia: {entrada}"
        assert entrada["despesas"] == pytest.approx(custo_folha_dia_esperado, abs=0.5)

        outro_dia = next(d for d in serie if d["data"] != dia_da_despesa_mirror)
        assert outro_dia["despesas"] == pytest.approx(custo_folha_dia_esperado, abs=0.5)
