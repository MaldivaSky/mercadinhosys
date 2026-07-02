"""
Reprodução do bug relatado: pedido de compra criado com item, mas a lista/detalhe
mostram "0 itens" (Total > 0 e 0 itens). Prova o ciclo criar → listar → detalhar.
"""
from decimal import Decimal

import pytest
from flask_jwt_extended import create_access_token

from app.models import db, Estabelecimento, Funcionario, CategoriaProduto, Produto, Fornecedor


def _headers(estab_id, func_id):
    token = create_access_token(identity=str(func_id), additional_claims={
        "estabelecimento_id": estab_id, "role": "admin",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ctx(session):
    estab = session.query(Estabelecimento).first()
    admin = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()
    forn = Fornecedor(estabelecimento_id=estab.id, nome_fantasia="LimpaTudo Atacado",
                      razao_social="LimpaTudo LTDA", cnpj="11222333000144")
    cat = CategoriaProduto(estabelecimento_id=estab.id, nome="Limpeza")
    session.add_all([forn, cat])
    session.flush()
    prod = Produto(estabelecimento_id=estab.id, categoria_id=cat.id, nome="Água Sanitária 2L",
                   preco_custo=Decimal("4.00"), preco_venda=Decimal("7.00"), quantidade=0)
    session.add(prod)
    session.commit()
    return {"estab": estab, "admin": admin, "forn": forn, "prod": prod}


def test_pedido_com_item_aparece_na_lista_e_detalhe(client, ctx):
    estab, admin, forn, prod = ctx["estab"], ctx["admin"], ctx["forn"], ctx["prod"]
    headers = _headers(estab.id, admin.id)

    # 1) Criar pedido com 1 item (Água Sanitária)
    r = client.post("/api/pedidos-compra/", json={
        "fornecedor_id": forn.id,
        "condicao_pagamento": "pix",
        "itens": [{"produto_id": prod.id, "quantidade": 12, "preco_unitario": 4.00, "desconto_percentual": 0}],
    }, headers=headers)
    assert r.status_code == 201, r.get_data(as_text=True)
    pedido = r.get_json()["pedido"]
    pedido_id = pedido["id"]

    # 2) LISTA deve mostrar o item (total_itens >= 1)
    rl = client.get("/api/pedidos-compra/", headers=headers)
    assert rl.status_code == 200, rl.get_data(as_text=True)
    pedidos = rl.get_json()["pedidos"]
    alvo = next((p for p in pedidos if p["id"] == pedido_id), None)
    assert alvo is not None, "pedido criado não apareceu na lista"
    assert alvo["total_itens"] == 1, f"lista mostrou {alvo['total_itens']} itens (esperado 1)"
    assert len(alvo["itens"]) == 1
    assert alvo["itens"][0]["produto_nome"] == "Água Sanitária 2L"

    # 3) DETALHE deve trazer o item
    rd = client.get(f"/api/pedidos-compra/{pedido_id}", headers=headers)
    assert rd.status_code == 200, rd.get_data(as_text=True)
    det = rd.get_json()
    itens = det.get("itens") or det.get("pedido", {}).get("itens")
    assert itens and len(itens) == 1, f"detalhe sem itens: {det}"
    assert Decimal(str(det.get("total") or det.get("pedido", {}).get("total"))) > 0
