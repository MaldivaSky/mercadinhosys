"""
Teste end-to-end da emissão de NFC-e (modelo 65) em modo SIMULADO.

Prova que toda a cadeia funciona pela API real: criar venda -> emitir NFC-e ->
listar documento -> cancelar. Em simulado não há valor fiscal, mas o fluxo,
a numeração, a idempotência e o cancelamento são os mesmos do gateway real
(Focus NFe) — basta o lojista plugar gateway='focusnfe' + token + CSC.
"""
import pytest
from decimal import Decimal
from flask_jwt_extended import create_access_token

from app.models import db, Estabelecimento, Produto, CategoriaProduto, Venda, DocumentoFiscal


def _setup_venda(client, session):
    estab = session.query(Estabelecimento).first()
    cat = CategoriaProduto.query.filter_by(estabelecimento_id=estab.id).first()
    if not cat:
        cat = CategoriaProduto(nome="Geral", estabelecimento_id=estab.id)
        session.add(cat)
        session.flush()
    prod = Produto(
        estabelecimento_id=estab.id, categoria_id=cat.id, nome="Refrigerante 2L",
        preco_custo=Decimal("5.00"), preco_venda=Decimal("8.00"), quantidade=100,
        ncm="22021000", cfop_padrao="5102", csosn="102",
    )
    session.add(prod)
    session.commit()

    token = create_access_token(identity="1", additional_claims={"estabelecimento_id": estab.id})
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "items": [{"productId": prod.id, "quantity": 2, "price": 8.00}],
        "subtotal": 16.00, "total": 16.00,
        "pagamentos": [{"forma_pagamento": "dinheiro", "valor": 16.00}],
    }
    resp = client.post("/api/vendas/", json=payload, headers=headers)
    assert resp.status_code in (200, 201), resp.get_data(as_text=True)
    codigo = resp.get_json()["venda"]["codigo"]
    venda = db.session.query(Venda).filter_by(codigo=codigo).first()
    return estab, venda, headers


def test_emitir_nfce_simulado_autorizado(client, session):
    estab, venda, headers = _setup_venda(client, session)
    numero_antes = int(getattr(estab, "proximo_numero_nfce", 1) or 1)

    resp = client.post(f"/api/fiscal/vendas/{venda.id}/nfce", headers=headers)
    assert resp.status_code == 201, resp.get_data(as_text=True)
    doc = resp.get_json()["documento"]
    assert doc["status"] == "autorizado"
    assert doc["chave_acesso"] and len(doc["chave_acesso"]) == 44
    assert doc["modelo"] == "65"

    # Numeração do estabelecimento avança após autorizar
    db.session.refresh(estab)
    assert int(estab.proximo_numero_nfce) == numero_antes + 1


def test_emitir_nfce_idempotente(client, session):
    estab, venda, headers = _setup_venda(client, session)
    r1 = client.post(f"/api/fiscal/vendas/{venda.id}/nfce", headers=headers)
    r2 = client.post(f"/api/fiscal/vendas/{venda.id}/nfce", headers=headers)
    assert r1.status_code == 201 and r2.status_code == 201
    # Mesma chave: não emite duas notas para a mesma venda
    assert r1.get_json()["documento"]["chave_acesso"] == r2.get_json()["documento"]["chave_acesso"]
    total_docs = DocumentoFiscal.query.filter_by(estabelecimento_id=estab.id, venda_id=venda.id).count()
    assert total_docs == 1


def test_listar_e_cancelar_nfce(client, session):
    estab, venda, headers = _setup_venda(client, session)
    emit = client.post(f"/api/fiscal/vendas/{venda.id}/nfce", headers=headers)
    doc_id = emit.get_json()["documento"]["id"]

    lst = client.get("/api/fiscal/documentos", headers=headers)
    assert lst.status_code == 200
    assert any(d["id"] == doc_id for d in lst.get_json()["documentos"])

    # Justificativa curta é rejeitada (exigência SEFAZ: >= 15 caracteres)
    curto = client.post(f"/api/fiscal/documentos/{doc_id}/cancelar",
                        json={"justificativa": "erro"}, headers=headers)
    assert curto.status_code == 400

    # Justificativa válida cancela
    ok = client.post(f"/api/fiscal/documentos/{doc_id}/cancelar",
                     json={"justificativa": "Cancelamento por erro de digitacao no PDV"}, headers=headers)
    assert ok.status_code == 200
    assert ok.get_json()["documento"]["status"] == "cancelado"
