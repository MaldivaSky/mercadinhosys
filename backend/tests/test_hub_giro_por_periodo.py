"""
Pedido do Rafael (2026-07-18): o seletor de período do Hub do produto
(7d/30d/90d/1y/all) filtrava faturamento/quantidade vendida, mas VMD/cobertura/
classe de giro ficavam travados na janela fixa de 90 dias (fonte única de
giro_cache.py, usada por cards/lista). Decisão: só o Hub passa a acompanhar o
período escolhido; cards/lista continuam na janela fixa de 90d.
"""
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal

import pytest
from flask_jwt_extended import create_access_token

from app.models import (
    db, Estabelecimento, Funcionario, CategoriaProduto, Produto, Venda, VendaItem,
)


def _headers(estab_id, func_id):
    token = create_access_token(identity=str(func_id), additional_claims={
        "estabelecimento_id": estab_id, "role": "admin",
    })
    return {"Authorization": f"Bearer {token}"}


def test_giro_do_hub_acompanha_periodo_selecionado(app, client, session):
    estab = session.query(Estabelecimento).first()
    admin = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()
    cat = CategoriaProduto(estabelecimento_id=estab.id, nome="Mercearia")
    session.add(cat); session.flush()
    prod = Produto(
        estabelecimento_id=estab.id, categoria_id=cat.id, nome="Produto Giro Periodo",
        preco_custo=Decimal("5.00"), preco_venda=Decimal("9.00"), quantidade=100,
    )
    session.add(prod); session.flush()

    # Venda recente (3 dias atrás, dentro da janela de 7d) — 10 unidades.
    v_recente = Venda(
        estabelecimento_id=estab.id, funcionario_id=admin.id, codigo="V-GP-1",
        subtotal=Decimal("90.00"), total=Decimal("90.00"), status="finalizada",
        data_venda=datetime.now(timezone.utc) - timedelta(days=3),
    )
    session.add(v_recente); session.flush()
    session.add(VendaItem(
        venda_id=v_recente.id, produto_id=prod.id, estabelecimento_id=estab.id,
        produto_nome=prod.nome, quantidade=10,
        preco_unitario=Decimal("9.00"), total_item=Decimal("90.00"),
    ))

    # Venda antiga (60 dias atrás, fora da janela de 7d mas dentro de 90d) — 5 unidades.
    v_antiga = Venda(
        estabelecimento_id=estab.id, funcionario_id=admin.id, codigo="V-GP-2",
        subtotal=Decimal("45.00"), total=Decimal("45.00"), status="finalizada",
        data_venda=datetime.now(timezone.utc) - timedelta(days=60),
    )
    session.add(v_antiga); session.flush()
    session.add(VendaItem(
        venda_id=v_antiga.id, produto_id=prod.id, estabelecimento_id=estab.id,
        produto_nome=prod.nome, quantidade=5,
        preco_unitario=Decimal("9.00"), total_item=Decimal("45.00"),
    ))
    session.commit()

    headers = _headers(estab.id, admin.id)

    r_all = client.get(f"/api/produtos/{prod.id}/hub?periodo=all", headers=headers)
    assert r_all.status_code == 200
    dados_all = r_all.get_json()["produto"]
    # periodo=all usa a fonte única fixa (90d): as duas vendas entram (15 un).
    assert dados_all["quantidade_vendida"] == 15

    r_7d = client.get(f"/api/produtos/{prod.id}/hub?periodo=7d", headers=headers)
    assert r_7d.status_code == 200
    dados_7d = r_7d.get_json()["produto"]
    # periodo=7d só enxerga a venda recente (10 un) — faturamento já era assim.
    assert dados_7d["quantidade_vendida"] == 10

    # O GIRO agora também muda: vmd de 7d (10un / poucos dias) é bem maior que
    # o vmd de 90d fixo (15un / ~60 dias ativos) — antes ficavam IDÊNTICOS
    # porque o giro ignorava o período.
    assert dados_7d["vmd"] > dados_all["vmd"] * 2, (
        f"VMD do período 7d ({dados_7d['vmd']}) deveria refletir a janela curta, "
        f"não ficar travado no valor de 90d ({dados_all['vmd']})"
    )
