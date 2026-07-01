"""
Teste de INTEGRAÇÃO do ciclo offline → sync → cloud.

Diferente do test_sync_hybrid (que valida peças isoladas), aqui provamos as
COSTURAS do ciclo real:

  1. CAPTURA  — em modo offline, uma mutação real (Produto) é automaticamente
     enfileirada em SyncQueue pelo listener after_flush.
  2. ROUND-TRIP — o payload AUTO-GERADO da fila, aplicado pelo receiver cloud
     (_process_sync_data), recria o MESMO registro no destino (upsert por id).
  3. IDEMPOTÊNCIA — reaplicar o mesmo delta não duplica nem quebra.
  4. ISOLAMENTO — o registro sincronizado carrega seu estabelecimento_id e não
     vaza para outro tenant.

Se o payload de captura (obj.to_dict) não bastar para reinserir no destino
(ex.: coluna NOT NULL faltando), este teste falha — que é exatamente o tipo de
lacuna que precisamos pegar antes de distribuir.
"""
import os
from decimal import Decimal

import pytest

from app.models import (
    db, Estabelecimento, CategoriaProduto, Produto, SyncQueue, allow_all_tenants,
)
from app.routes.sync_cloud import _process_sync_data


@pytest.fixture
def offline_mode():
    """Ativa MERCADINHO_OFFLINE só durante o teste (o listener de captura depende dele)."""
    anterior = os.environ.get("MERCADINHO_OFFLINE")
    os.environ["MERCADINHO_OFFLINE"] = "true"
    try:
        yield
    finally:
        if anterior is None:
            os.environ.pop("MERCADINHO_OFFLINE", None)
        else:
            os.environ["MERCADINHO_OFFLINE"] = anterior


def _criar_produto(session, estab_id, nome, cat_nome):
    cat = CategoriaProduto(estabelecimento_id=estab_id, nome=cat_nome)
    session.add(cat)
    session.flush()
    p = Produto(
        estabelecimento_id=estab_id, categoria_id=cat.id, nome=nome,
        preco_venda=Decimal("25.00"), preco_custo=Decimal("18.00"), quantidade=50,
    )
    session.add(p)
    session.commit()
    return p


def test_captura_offline_enfileira_delta(session, offline_mode):
    estab = session.query(Estabelecimento).first()
    p = _criar_produto(session, estab.id, "Refrigerante 2L", "Bebidas")

    with allow_all_tenants():
        delta = SyncQueue.query.filter_by(tabela="produtos", registro_id=p.id).first()

    assert delta is not None, "modo offline deveria enfileirar a mutação em SyncQueue"
    assert delta.operacao == "insert"

    payload = delta.to_sync_payload()
    assert payload["tabela"] == "produtos"
    assert payload["registro_id"] == p.id
    assert payload["operacao"] == "INSERT"
    assert payload["estabelecimento_id"] == estab.id
    assert payload["payload"]["nome"] == "Refrigerante 2L"


def test_round_trip_offline_para_cloud_e_idempotente(session, offline_mode):
    estab = session.query(Estabelecimento).first()
    p = _criar_produto(session, estab.id, "Arroz 5kg", "Mercearia")
    pid = p.id

    with allow_all_tenants():
        delta = SyncQueue.query.filter_by(tabela="produtos", registro_id=pid).first()
    payload = delta.to_sync_payload()

    # Simula "o destino ainda não tem este registro": remove localmente.
    with allow_all_tenants():
        Produto.query.filter_by(id=pid).delete()
    session.commit()
    with allow_all_tenants():
        assert Produto.query.filter_by(id=pid).first() is None

    # Receiver cloud aplica o delta auto-gerado (upsert por registro_id).
    assert _process_sync_data(payload, session) is True, (
        "receiver não conseguiu persistir o payload de captura — provável coluna "
        "faltando no to_dict()"
    )
    session.commit()

    with allow_all_tenants():
        restaurado = Produto.query.filter_by(id=pid).first()
    assert restaurado is not None, "registro não chegou ao destino"
    assert restaurado.nome == "Arroz 5kg"
    assert restaurado.estabelecimento_id == estab.id
    assert float(restaurado.preco_venda) == 25.00

    # IDEMPOTÊNCIA: reaplicar o mesmo delta não duplica nem quebra.
    assert _process_sync_data(payload, session) is True
    session.commit()
    with allow_all_tenants():
        assert Produto.query.filter_by(id=pid).count() == 1


def test_sync_preserva_isolamento_de_tenant(session, offline_mode):
    """Um registro sincronizado pertence ao seu tenant e não aparece para outro."""
    estab_a = session.query(Estabelecimento).first()
    p = _criar_produto(session, estab_a.id, "Produto Loja A Sync", "Geral")
    pid = p.id

    with allow_all_tenants():
        payload = SyncQueue.query.filter_by(tabela="produtos", registro_id=pid).first().to_sync_payload()
        Produto.query.filter_by(id=pid).delete()
    session.commit()

    assert _process_sync_data(payload, session) is True
    session.commit()

    # Consulta escopada a OUTRO tenant (id diferente) não pode ver o produto.
    from flask import g
    outro_tid = estab_a.id + 99999
    g.estabelecimento_id = outro_tid
    try:
        assert Produto.query.filter_by(id=pid).first() is None, (
            "VAZAMENTO: produto sincronizado apareceu para outro tenant"
        )
    finally:
        if hasattr(g, "estabelecimento_id"):
            delattr(g, "estabelecimento_id")
