"""
Testes do PIN de segurança (definir no Settings + verificar para gate de
editar/descartar produto). Mesma infra do estorno (Funcionario.pin_cancelamento).
"""
import pytest
from flask_jwt_extended import create_access_token

from app.models import db, Estabelecimento, Funcionario


def _admin(session):
    from flask import g, has_request_context
    estab = session.query(Estabelecimento).first()
    # Espelha um request autenticado: sem tenant em g, o guard multi-tenant
    # (fail-closed) filtra as queries por estabelecimento_id = -1 e o seed some.
    if has_request_context():
        g.estabelecimento_id = estab.id
    func = session.query(Funcionario).filter_by(estabelecimento_id=estab.id).first()
    func.nivel_acesso = 1  # admin (em produção já é 1; conftest cria como 3)
    db.session.commit()
    return estab, func


def _token(estab_id, role="admin", nivel=1, uid="1"):
    return {"Authorization": f"Bearer " + create_access_token(
        identity=uid, additional_claims={"estabelecimento_id": estab_id, "role": role, "nivel_acesso": nivel})}


def test_admin_define_pin(client, session):
    estab, func = _admin(session)
    r = client.put("/api/configuracao/pin", json={"pin": "4321"}, headers=_token(estab.id))
    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.get_json()["tem_pin"] is True
    db.session.refresh(func)
    assert func.tem_pin and func.check_pin("4321")


def test_pin_invalido_rejeitado(client, session):
    estab, _ = _admin(session)
    for ruim in ["12", "12ab", "1234567"]:
        r = client.put("/api/configuracao/pin", json={"pin": ruim}, headers=_token(estab.id))
        assert r.status_code == 400, f"PIN {ruim!r} deveria ser rejeitado"


def test_nao_admin_nao_define_pin(client, session):
    estab, _ = _admin(session)
    r = client.put("/api/configuracao/pin", json={"pin": "4321"},
                   headers=_token(estab.id, role="caixa", nivel=3))
    assert r.status_code == 403


def test_verificar_pin(client, session):
    estab, func = _admin(session)
    func.set_pin("4321")
    db.session.commit()

    ok = client.post("/api/configuracao/verificar-pin", json={"pin": "4321"}, headers=_token(estab.id))
    assert ok.status_code == 200 and ok.get_json()["success"] is True

    nao = client.post("/api/configuracao/verificar-pin", json={"pin": "0000"}, headers=_token(estab.id))
    assert nao.status_code == 403


def test_gate_funciona_para_qualquer_operador_com_pin_do_admin(client, session):
    """Um caixa (nível 3) consegue VERIFICAR o PIN do admin — é o gate de autorização."""
    estab, admin = _admin(session)
    admin.set_pin("4321")
    db.session.commit()
    # operador caixa envia o PIN do admin para autorizar a operação
    r = client.post("/api/configuracao/verificar-pin", json={"pin": "4321"},
                    headers=_token(estab.id, role="caixa", nivel=3))
    assert r.status_code == 200 and r.get_json()["success"] is True
