from flask_jwt_extended import create_access_token

from app.models import Funcionario


def test_clientes_rfm_retorna_200_sem_explodir(client, app, session):
    with app.app_context():
        # Espelha tenant autenticado: sem g, o guard fail-closed filtra por -1.
        from flask import g, has_request_context
        from app.models import Estabelecimento
        _estab = Estabelecimento.query.first()
        if has_request_context() and _estab:
            g.estabelecimento_id = _estab.id
        admin = Funcionario.query.filter_by(ativo=True).first()
        assert admin is not None
        token = create_access_token(
            identity=str(admin.id),
            additional_claims={
                "estabelecimento_id": admin.estabelecimento_id,
                "role": admin.role,
                "is_super_admin": bool(getattr(admin, "is_super_admin", False)),
            },
        )

    response = client.get(
        "/api/clientes/rfm",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "rfm" in data
