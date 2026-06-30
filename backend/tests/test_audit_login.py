"""
Prova que o LOGIN gera um evento de auditoria (tipo_evento='login').

Antes deste fix, o login real (auth_multi_tenant) não auditava — então o painel
de super admin (monitor) nunca mostrava 'fulano logou'. Este teste trava isso.
"""
from datetime import date
from decimal import Decimal

from app import db
from app.models import Funcionario, Estabelecimento, Auditoria


def test_login_gera_evento_de_auditoria(client, session):
    estab = session.query(Estabelecimento).first()

    user = Funcionario(
        estabelecimento_id=estab.id,
        nome="Lojista Teste",
        cpf="99988877766",
        username="lojista_audit",
        role="ADMIN",
        status="ativo",
        ativo=True,
        data_nascimento=date(1990, 1, 1),
        celular="92999999999",
        email="lojista_audit@teste.sys",
        cargo="Dono",
        data_admissao=date(2024, 1, 1),
        salario_base=Decimal("1000.00"),
    )
    user.set_password("senha123")
    db.session.add(user)
    db.session.commit()

    resp = client.post("/api/auth/login", json={"identifier": "lojista_audit", "senha": "senha123"})
    assert resp.status_code == 200, resp.get_data(as_text=True)

    log = (
        db.session.query(Auditoria)
        .filter_by(tipo_evento="login", estabelecimento_id=estab.id)
        .first()
    )
    assert log is not None, "Login não gerou evento de auditoria (monitor ficaria vazio)"
    assert log.usuario_id == user.id
