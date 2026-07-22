"""
Testes Unitários do Módulo de Conformidade LGPD (/api/lgpd/delete)
"""

import pytest
from datetime import date
from flask_jwt_extended import create_access_token
from app import db
from app.models import Estabelecimento, Cliente, Funcionario, Auditoria


@pytest.fixture
def ambiente_lgpd(session):
    """Cria estabelecimento, clientes e funcionários para teste LGPD."""
    estab = Estabelecimento(
        nome_fantasia="Loja LGPD Test",
        razao_social="Loja LGPD LTDA",
        cnpj="11222333000199",
        email="contato@lgpdtest.com",
        telefone="92977777777",
        plano="PRO",
        cep="69000-000",
        logradouro="Rua Teste",
        numero="100",
        bairro="Centro",
        cidade="Manaus",
        estado="AM",
        pais="Brasil",
    )
    db.session.add(estab)
    db.session.flush()

    cliente = Cliente(
        estabelecimento_id=estab.id,
        nome="Cliente Sensível Silva",
        cpf="123.456.789-00",
        email="sensivel@gmail.com",
        telefone="92999990000",
        celular="92999990000",
        cep="69000-000",
        logradouro="Rua Sensível",
        numero="10",
        bairro="Centro",
        cidade="Manaus",
        estado="AM",
        pais="Brasil",
    )
    
    func_inativo = Funcionario(
        estabelecimento_id=estab.id,
        nome="Funcionário Demitido",
        cpf="987.654.321-11",
        email="demitido@empresa.com",
        username="ex_func_01",
        senha="hashed_password_123",
        cargo="Operador Ex",
        telefone="92988888888",
        celular="92988888888",
        data_nascimento=date(1990, 1, 1),
        data_admissao=date(2023, 1, 1),
        ativo=False,
    )

    func_admin = Funcionario(
        estabelecimento_id=estab.id,
        nome="Administrador LGPD",
        cpf="111.222.333-44",
        email="admin@empresa.com",
        username="admin_lgpd",
        senha="hashed_password_admin",
        cargo="Administrador",
        role="admin",
        telefone="92988888888",
        celular="92988888888",
        data_nascimento=date(1985, 5, 15),
        data_admissao=date(2020, 1, 1),
        ativo=True,
    )

    db.session.add_all([cliente, func_inativo, func_admin])
    db.session.commit()

    return estab, cliente, func_inativo, func_admin


def test_lgpd_delete_exige_confirmacao(client, ambiente_lgpd):
    estab, cliente, func_inativo, func_admin = ambiente_lgpd
    token = create_access_token(
        identity=str(func_admin.id),
        additional_claims={"estabelecimento_id": estab.id, "role": "admin", "is_super_admin": False},
    )

    # Chamada sem campo confirmacao
    resp = client.post(
        "/api/lgpd/delete",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "confirmacao" in resp.get_json()["message"].lower()


def test_lgpd_delete_anonimiza_com_sucesso(client, ambiente_lgpd):
    estab, cliente, func_inativo, func_admin = ambiente_lgpd
    token = create_access_token(
        identity=str(func_admin.id),
        additional_claims={"estabelecimento_id": estab.id, "role": "admin", "is_super_admin": False},
    )

    resp = client.post(
        "/api/lgpd/delete",
        json={"confirmacao": "EXCLUIR_DADOS_LGPD"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["estatisticas"]["clientes_anonimizados"] >= 1

    # Verificar anonimização no banco
    cliente_db = Cliente.query.get(cliente.id)
    assert cliente_db.nome.startswith("Cliente Anonimizado LGPD")
    assert cliente_db.cpf == "000.000.000-00"
    assert "lgpd.local" in cliente_db.email

    # Verificar registro de auditoria
    log = Auditoria.query.filter_by(estabelecimento_id=estab.id, tipo_evento="LGPD_EXCLUSAO_DADOS").first()
    assert log is not None
    assert "LGPD" in log.tipo_evento
