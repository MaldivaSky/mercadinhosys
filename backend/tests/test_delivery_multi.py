import pytest
from app.models import Venda, Pagamento, Produto, Estabelecimento, Motorista, Veiculo, Cliente, Entrega, CategoriaProduto
from flask_jwt_extended import create_access_token
from decimal import Decimal

def test_venda_entrega_multi_pagamento_sucesso(client, session):
    # Get official establishment from conftest
    estab = session.query(Estabelecimento).first()
    assert estab is not None
    
    cat = CategoriaProduto(nome="Geral", estabelecimento_id=estab.id)
    session.add(cat)
    session.flush()
    
    prod = Produto(
        estabelecimento_id=estab.id,
        categoria_id=cat.id,
        nome="Pizza Calabresa",
        preco_venda=45.00,
        preco_custo=20.00,
        quantidade=50
    )
    session.add(prod)

    # Motorista and Veiculo
    mot = Motorista(
        estabelecimento_id=estab.id, 
        nome="Flash Entregador", 
        cpf="12345678901", 
        cnh="123456789", 
        telefone="92988888888", 
        celular="92999999999",
        ativo=True
    )
    vei = Veiculo(
        estabelecimento_id=estab.id, 
        tipo="MOTO", 
        placa="ABC1234", 
        marca="Honda", 
        modelo="CG 160", 
        consumo_medio=30
    )
    session.add_all([mot, vei])

    cust = Cliente(
        nome="Cliente Delivery",
        cpf="98765432100",
        estabelecimento_id=estab.id,
        cep="01001-000",
        logradouro="Rua Delivery",
        numero="500",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP"
    )
    session.add(cust)
    session.commit()

    token = create_access_token(identity="1", additional_claims={"estabelecimento_id": estab.id})
    headers = {"Authorization": f"Bearer {token}"}

    # Total: Pizza (45) + Taxa (5) = 50.00
    # Pagamento: R$ 20.00 Dinheiro + R$ 30.00 Cartão
    payload = {
        "cliente_id": cust.id,
        "itens": [
            {"produto_id": prod.id, "quantidade": 1, "preco_unitario": 45.00}
        ],
        "subtotal": 45.00,
        "total": 50.00,
        "taxa_entrega": 5.00,
        "motorista_id": mot.id,
        "veiculo_id": vei.id,
        "pagamentos": [
            {"forma_pagamento": "dinheiro", "valor": 20.00},
            {"forma_pagamento": "cartao_credito", "valor": 30.00}
        ],
        "endereco_cep": "00000-000",
        "endereco_logradouro": "Rua de Cima",
        "endereco_numero": "123",
        "endereco_bairro": "Centro"
    }

    response = client.post("/delivery/venda-entrega", json=payload, headers=headers)
    assert response.status_code == 201 or response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    # Verify Database State
    venda = db.session.query(Venda).filter_by(codigo=data["codigo"]).first()
    assert venda is not None
    assert float(venda.total) == 50.00
    assert len(venda.pagamentos) == 2
    
    # Check if Entrega was created
    entrega = Entrega.query.filter_by(venda_id=venda.id).first()
    assert entrega is not None
    assert entrega.motorista_id == mot.id
    assert float(venda.total) == 50.00
