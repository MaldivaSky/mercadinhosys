"""
Regressão: o card do dashboard ("Classe A: 4") deve bater com o número de produtos
que o modal lista ao clicar nele (filtro_rapido=classe_a). Antes divergiam porque o
card lia a coluna estática `classificacao_abc` e o filtro recalculava dinamicamente.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from flask_jwt_extended import create_access_token
from app.models import (
    Estabelecimento, CategoriaProduto, Produto, Venda, VendaItem, Funcionario, db
)


def _auth(estab_id):
    token = create_access_token(identity="1", additional_claims={"estabelecimento_id": estab_id})
    return {"Authorization": f"Bearer {token}"}


def test_card_abc_bate_com_lista_filtrada(client, session):
    estab = session.query(Estabelecimento).first()
    func_id = session.query(Funcionario).first().id
    cat = CategoriaProduto(nome="Geral", estabelecimento_id=estab.id)
    session.add(cat)
    session.flush()

    # 5 produtos: faturamentos bem distintos para gerar A/B/C previsível.
    produtos = []
    for i, preco in enumerate([100, 50, 10, 5, 1], start=1):
        p = Produto(
            estabelecimento_id=estab.id, categoria_id=cat.id,
            nome=f"Produto {i}", preco_custo=Decimal("1.00"),
            preco_venda=Decimal(str(preco)), quantidade=1000,
            classificacao_abc="C",  # coluna estática propositalmente "errada"
        )
        produtos.append(p)
    session.add_all(produtos)
    session.flush()

    # Uma venda finalizada com 1 unidade de cada → faturamento = preço de venda.
    venda = Venda(
        estabelecimento_id=estab.id, funcionario_id=func_id, codigo="V-ABC-1",
        subtotal=Decimal("166"), total=Decimal("166"),
        status="finalizada", data_venda=datetime.utcnow() - timedelta(days=1),
    )
    session.add(venda)
    session.flush()
    for p in produtos:
        session.add(VendaItem(
            venda_id=venda.id, produto_id=p.id, estabelecimento_id=estab.id,
            produto_nome=p.nome, quantidade=1,
            preco_unitario=p.preco_venda, total_item=p.preco_venda,
        ))
    session.commit()

    headers = _auth(estab.id)

    # 1) Card do dashboard
    resp_stats = client.get("/api/produtos/estatisticas", headers=headers)
    assert resp_stats.status_code == 200, resp_stats.get_data(as_text=True)
    abc = resp_stats.get_json()["estatisticas"]["classificacao_abc"]

    # 2) Lista filtrada como o modal faz, para cada classe
    for classe, filtro in [("A", "classe_a"), ("B", "classe_b"), ("C", "classe_c")]:
        resp_lista = client.get(
            f"/api/produtos/?filtro_rapido={filtro}&por_pagina=100", headers=headers
        )
        assert resp_lista.status_code == 200, resp_lista.get_data(as_text=True)
        body = resp_lista.get_json()
        lista = body.get("produtos", body.get("data", []))
        assert abc[classe] == len(lista), (
            f"Classe {classe}: card diz {abc[classe]} mas a lista retornou {len(lista)}"
        )

    # Sanidade: todos os 5 produtos classificados em alguma classe.
    assert abc["A"] + abc["B"] + abc["C"] == 5
