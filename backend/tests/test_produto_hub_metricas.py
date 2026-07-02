"""
Bug relatado: uma venda com o produto existe (ex.: DOCE DE LEITE), mas o HUB do
produto mostra faturamento R$ 0,00 / "sem vendas" / "null dias atrás".

Causa: o HUB lia colunas denormalizadas (total_vendido/quantidade_vendida/
ultima_venda) que a venda NÃO atualizava. Fix: o HUB agrega ao vivo de
venda_itens (fonte da verdade). Este teste prova que a venda aparece no HUB.
"""
from datetime import datetime, timezone
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


def test_hub_reflete_venda_real_do_produto(client, session):
    estab = session.query(Estabelecimento).first()
    admin = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()
    cat = CategoriaProduto(estabelecimento_id=estab.id, nome="Mercearia")
    session.add(cat); session.flush()
    prod = Produto(
        estabelecimento_id=estab.id, categoria_id=cat.id, nome="Doce de Leite Itambé 350g",
        preco_custo=Decimal("6.00"), preco_venda=Decimal("9.37"), quantidade=24,
        # denorm propositalmente zerado — o HUB NÃO pode depender disso
        total_vendido=0, quantidade_vendida=0, ultima_venda=None,
    )
    session.add(prod); session.flush()

    # Venda finalizada de 1 unidade
    venda = Venda(
        estabelecimento_id=estab.id, funcionario_id=admin.id, codigo="V-HUB-1",
        subtotal=Decimal("9.37"), total=Decimal("9.37"), status="finalizada",
        data_venda=datetime.now(timezone.utc),
    )
    session.add(venda); session.flush()
    session.add(VendaItem(
        venda_id=venda.id, produto_id=prod.id, estabelecimento_id=estab.id,
        produto_nome=prod.nome, quantidade=1,
        preco_unitario=Decimal("9.37"), total_item=Decimal("9.37"),
    ))
    session.commit()

    r = client.get(f"/api/produtos/{prod.id}/hub", headers=_headers(estab.id, admin.id))
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json()

    # Faturamento e quantidade têm de refletir a venda real
    assert float(data["produto"]["total_vendido"]) == pytest.approx(9.37), data["produto"]
    assert float(data["produto"]["quantidade_vendida"]) == 1
    assert data["produto"]["ultima_venda"] is not None, "última venda deveria estar preenchida"
    assert data["estatisticas"]["valor_total_vendido"] == pytest.approx(9.37)
    assert data["estatisticas"]["dias_sem_venda"] is not None


def test_hub_ignora_venda_cancelada(client, session):
    estab = session.query(Estabelecimento).first()
    admin = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()
    cat = CategoriaProduto(estabelecimento_id=estab.id, nome="Cat")
    session.add(cat); session.flush()
    prod = Produto(estabelecimento_id=estab.id, categoria_id=cat.id, nome="Produto Cancelado",
                   preco_custo=Decimal("1"), preco_venda=Decimal("2"), quantidade=10)
    session.add(prod); session.flush()
    venda = Venda(estabelecimento_id=estab.id, funcionario_id=admin.id, codigo="V-HUB-CANC",
                  subtotal=Decimal("2"), total=Decimal("2"), status="cancelada",
                  data_venda=datetime.now(timezone.utc))
    session.add(venda); session.flush()
    session.add(VendaItem(venda_id=venda.id, produto_id=prod.id, estabelecimento_id=estab.id,
                          produto_nome=prod.nome, quantidade=1,
                          preco_unitario=Decimal("2"), total_item=Decimal("2")))
    session.commit()

    r = client.get(f"/api/produtos/{prod.id}/hub", headers=_headers(estab.id, admin.id))
    assert r.status_code == 200
    assert float(r.get_json()["produto"]["total_vendido"]) == 0.0, "venda cancelada não conta"
