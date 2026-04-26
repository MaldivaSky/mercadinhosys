import pytest
from app.models import Venda, Pagamento, Produto, Estabelecimento, CategoriaProduto, Cliente, db
from flask_jwt_extended import create_access_token

def test_venda_multi_pagamento_sucesso(client, session):
    # Get the official test establishment from conftest fixture
    estab = session.query(Estabelecimento).first()
    assert estab is not None
    
    # Create Mandatory Category for this establishment
    cat = CategoriaProduto(nome="Geral", estabelecimento_id=estab.id)
    session.add(cat)
    session.flush()

    # Create test products
    prod = Produto(
        estabelecimento_id=estab.id,
        categoria_id=cat.id,
        nome="Arroz 5kg Industrial",
        preco_custo=20.00,
        preco_venda=35.90,
        quantidade=100
    )
    prod2 = Produto(
        estabelecimento_id=estab.id,
        categoria_id=cat.id,
        nome="Feijão 1kg Preto",
        preco_custo=5.00,
        preco_venda=8.90,
        quantidade=100
    )
    session.add_all([prod, prod2])

    # Create Mandatory Customer with Address
    cust = Cliente(
        nome="Cliente Teste",
        cpf="12345678901",
        estabelecimento_id=estab.id,
        celular="11999999999",
        cep="01001-000",
        logradouro="Rua Teste",
        numero="1",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP"
    )
    session.add(cust)
    session.commit()

    # Generate JWT for the test user
    token = create_access_token(identity="1", additional_claims={"estabelecimento_id": estab.id})
    headers = {"Authorization": f"Bearer {token}"}

    # Payload split: R$ 50,00 total (Arroz + algo mais imaginário)
    # Vamos fazer uma venda de R$ 71.80 (2 Arroz)
    # Pagamento: R$ 40 em Dinheiro + R$ 31.80 em PIX
    payload = {
        "items": [
            {"productId": prod.id, "quantity": 2, "price": 35.90}
        ],
        "subtotal": 71.80,
        "desconto": 0,
        "total": 71.80,
        "pagamentos": [
            {"forma_pagamento": "dinheiro", "valor": 40.00},
            {"forma_pagamento": "pix", "valor": 31.80}
        ]
    }

    response = client.post("/api/vendas/", json=payload, headers=headers)
    assert response.status_code == 201 or response.status_code == 200
    data = response.get_json()
    assert "venda" in data
    assert "codigo" in data["venda"]
    
    # Verify Database State (Bypass TenantQuery Filters in Test)
    venda = db.session.query(Venda).filter_by(codigo=data["venda"]["codigo"]).first()
    assert venda is not None
    assert float(venda.total) == 71.80
    assert len(venda.pagamentos) == 2
    
    formas = [p.forma_pagamento for p in venda.pagamentos]
    assert "dinheiro" in formas
    assert "pix" in formas
    
    total_pg = sum(p.valor for p in venda.pagamentos)
    assert float(total_pg) == 71.80

def test_venda_valor_insuficiente_erro(client, session):
    estab = session.query(Estabelecimento).first()
    if not estab:
        estab = Estabelecimento(nome="Teste Insuficiente", plano="Pro")
        session.add(estab)
        session.flush()
    
    cat = CategoriaProduto.query.filter_by(estabelecimento_id=estab.id).first()
    if not cat:
        cat = CategoriaProduto(nome="Geral", estabelecimento_id=estab.id)
        session.add(cat)
        session.flush()

    prod = Produto(
        estabelecimento_id=estab.id,
        categoria_id=cat.id,
        nome="Produto Teste Erro",
        preco_custo=20.00,
        preco_venda=35.90,
        quantidade=100
    )
    session.add(prod)
    session.commit()

    token = create_access_token(identity="1", additional_claims={"estabelecimento_id": estab.id})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "items": [{"productId": prod.id, "quantity": 1, "price": 35.90}],
        "subtotal": 35.90,
        "total": 35.90,
        "pagamentos": [
            {"forma_pagamento": "dinheiro", "valor": 20.00} # Faltando dinheiro
        ]
    }

    response = client.post("/api/vendas/", json=payload, headers=headers)
    assert response.status_code == 400
    assert "menor que o total da venda" in response.get_json()["error"]
