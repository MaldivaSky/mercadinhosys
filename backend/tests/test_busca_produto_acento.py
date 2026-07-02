"""
Bug relatado: produto cadastrado (ex.: "Água Sanitária Supreme") não aparece na
busca do modal de pedido. Testa a busca real de /produtos/ por nome COM e SEM
acento e por trecho — o mecanismo que o modal usa.
"""
from decimal import Decimal

import pytest
from flask_jwt_extended import create_access_token

from app.models import db, Estabelecimento, Funcionario, CategoriaProduto, Produto


def _headers(estab_id, func_id):
    token = create_access_token(identity=str(func_id), additional_claims={
        "estabelecimento_id": estab_id, "role": "admin",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ctx(session):
    estab = session.query(Estabelecimento).first()
    admin = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()
    cat = CategoriaProduto(estabelecimento_id=estab.id, nome="Limpeza")
    session.add(cat); session.flush()
    p = Produto(estabelecimento_id=estab.id, categoria_id=cat.id,
                nome="Água Sanitária Supreme", codigo_barras="7891000055120",
                preco_custo=Decimal("4.00"), preco_venda=Decimal("7.00"), quantidade=0, ativo=True)
    session.add(p); session.commit()
    return {"estab": estab, "admin": admin, "prod": p}


@pytest.mark.parametrize("termo", ["Água", "Sanitária", "Supreme", "gua San", "7891000055120"])
def test_busca_encontra_produto_cadastrado(client, ctx, termo):
    r = client.get(f"/api/produtos/?busca={termo}&por_pagina=20", headers=_headers(ctx["estab"].id, ctx["admin"].id))
    assert r.status_code == 200, r.get_data(as_text=True)
    nomes = [p["nome"] for p in r.get_json().get("produtos", [])]
    assert ctx["prod"].nome in nomes, f"busca '{termo}' não achou o produto. Retornou: {nomes}"


@pytest.mark.parametrize("termo", ["agua", "AGUA", "sanitaria", "SANITARIA"])
def test_busca_sem_acento_encontra_nome_com_acento(client, ctx, termo):
    """Digitar sem acento (comum no dia a dia) deve achar o nome acentuado."""
    r = client.get(f"/api/produtos/?busca={termo}&por_pagina=20", headers=_headers(ctx["estab"].id, ctx["admin"].id))
    assert r.status_code == 200, r.get_data(as_text=True)
    nomes = [p["nome"] for p in r.get_json().get("produtos", [])]
    assert ctx["prod"].nome in nomes, f"busca sem acento '{termo}' não achou 'Água Sanitária'. Retornou: {nomes}"
