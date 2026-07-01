"""
SMOKE TEST do fluxo de demonstração — caminha o happy-path que o Rafael mostra
para o cliente, batendo nos ENDPOINTS REAIS da API:

    cadastrar cliente → cadastrar produto → abrir venda → emitir comprovante

Se qualquer um quebrar, a demo quebra. Este teste é a prova de que não quebra.
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from flask_jwt_extended import create_access_token

from app.models import (
    db, Estabelecimento, Funcionario, CategoriaProduto, Produto, Caixa,
)


def _headers(estab_id, func_id):
    token = create_access_token(identity=str(func_id), additional_claims={
        "estabelecimento_id": estab_id, "role": "admin", "nome": "Admin Demo",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ctx(session):
    """Contexto de demo: loja, admin, caixa ABERTO (venda exige) e categoria."""
    estab = session.query(Estabelecimento).first()
    admin = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()

    caixa = Caixa(
        estabelecimento_id=estab.id, funcionario_id=admin.id,
        numero_caixa="PDV-01", saldo_inicial=Decimal("100"), saldo_atual=Decimal("100"),
        status="aberto", data_abertura=datetime.now(timezone.utc),
    )
    cat = CategoriaProduto(estabelecimento_id=estab.id, nome="Geral")
    session.add_all([caixa, cat])
    session.commit()
    return {"estab": estab, "admin": admin, "cat": cat}


def test_demo_cadastrar_cliente(client, ctx):
    r = client.post("/api/clientes/", json={
        "nome": "Cliente Demonstração",
        "cpf": "390.533.447-05",   # CPF válido
        "celular": "(92) 99123-4567",
        "email": "cliente@demo.com",
    }, headers=_headers(ctx["estab"].id, ctx["admin"].id))
    assert r.status_code in (200, 201), r.get_data(as_text=True)
    assert r.get_json().get("success") is not False


def test_demo_cadastrar_produto(client, ctx):
    r = client.post("/api/produtos/", json={
        "nome": "Refrigerante Cola 2L",
        "categoria": "Geral",
        "preco_custo": 4.50,
        "preco_venda": 8.90,
        "quantidade": 100,
        "codigo_barras": "7890000000017",
    }, headers=_headers(ctx["estab"].id, ctx["admin"].id))
    assert r.status_code in (200, 201), r.get_data(as_text=True)
    assert r.get_json().get("success") is not False


def test_demo_venda_e_comprovante(client, ctx):
    estab, admin = ctx["estab"], ctx["admin"]
    # Produto para vender (via ORM p/ isolar o teste da venda em si)
    p = Produto(
        estabelecimento_id=estab.id, categoria_id=ctx["cat"].id,
        nome="Pão Francês", preco_custo=Decimal("0.30"), preco_venda=Decimal("0.75"),
        quantidade=500,
    )
    db.session.add(p)
    db.session.commit()

    headers = _headers(estab.id, admin.id)

    # 1) Finalizar venda pelo PDV (dinheiro)
    venda_payload = {
        "items": [{"id": p.id, "quantity": 4, "price": 0.75}],
        "subtotal": 3.00, "desconto": 0, "total": 3.00,
        "pagamentos": [{"forma": "dinheiro", "valor": 5.00}],
        "valor_recebido": 5.00, "troco": 2.00,
    }
    r = client.post("/api/pdv/finalizar", json=venda_payload, headers=headers)
    assert r.status_code in (200, 201), r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("success") is not False, body
    venda = body.get("venda") or body.get("data") or {}
    venda_id = venda.get("id") or body.get("id")
    assert venda_id, f"venda sem id: {body}"

    # 2) Emitir/visualizar o comprovante da venda
    r2 = client.get(f"/api/pdv/comprovante/{venda_id}", headers=headers)
    assert r2.status_code == 200, r2.get_data(as_text=True)
    comp = r2.get_json()
    assert comp.get("success") is True
    assert len(comp["comprovante"]["itens"]) >= 1
    # Lei da Transparência: o comprovante carrega o campo de tributos (mesmo que 0).
    assert "valor_tributos" in comp["comprovante"]


def test_demo_venda_bloqueada_sem_caixa(client, session):
    """Regra de negócio: sem caixa aberto, a venda é bloqueada (não some silenciosa)."""
    estab = session.query(Estabelecimento).first()
    # Funcionário SEM caixa aberto
    admin = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()
    cat = CategoriaProduto(estabelecimento_id=estab.id, nome="Sem Caixa")
    session.add(cat); session.flush()
    p = Produto(estabelecimento_id=estab.id, categoria_id=cat.id, nome="Item",
                preco_custo=Decimal("1"), preco_venda=Decimal("2"), quantidade=10)
    session.add(p); session.commit()

    r = client.post("/api/pdv/finalizar", json={
        "items": [{"id": p.id, "quantity": 1, "price": 2.0}],
        "subtotal": 2.0, "total": 2.0,
        "pagamentos": [{"forma": "dinheiro", "valor": 2.0}],
    }, headers=_headers(estab.id, admin.id))
    assert r.status_code == 403
    assert r.get_json().get("error") == "CAIXA_FECHADO"
