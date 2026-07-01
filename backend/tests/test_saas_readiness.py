import pytest
from datetime import date
from app.decorators.plan_guards import plan_required, premium_required
from flask import jsonify

def test_plan_hierarchy_normalization(session):
    # This test checks if normalization works as expected in plan_guards logic
    from app.decorators.plan_guards import normalize_plan
    assert normalize_plan("Premium") == "Premium"
    assert normalize_plan("PRO") == "Premium"
    assert normalize_plan("Gratuito") == "Gratuito"
    assert normalize_plan("Basic") == "Gratuito"

def test_premium_required_decorator(app, client, session):
    from app.models import Estabelecimento, Funcionario
    from flask_jwt_extended import create_access_token
    
    @premium_required
    def premium_route():
        return jsonify(success=True)

    # 1. Create a "Gratuito" account
    estab_free = Estabelecimento.query.first()
    estab_free.plano = "Gratuito"
    estab_free.plano_status = "ativo"

    # Espelha request autenticado: sem tenant em g o guard fail-closed filtra
    # Funcionario por estabelecimento_id = -1 e o admin some.
    from flask import g, has_request_context
    if has_request_context():
        g.estabelecimento_id = estab_free.id

    admin = Funcionario.query.filter_by(estabelecimento_id=estab_free.id).first()
    token_free = create_access_token(identity=str(admin.id), additional_claims={
        "is_super_admin": False,
        "estabelecimento_id": estab_free.id,
        "role": "admin"
    })
    
    headers_free = {"Authorization": f"Bearer {token_free}"}
    with app.test_request_context('/test-premium', headers=headers_free):
        response = app.make_response(premium_route())
    assert response.status_code == 403
    assert "upgrade" in response.get_json()['msg'].lower()

    # 2. Upgrade to Premium
    estab_free.plano = "Premium"
    import sqlalchemy as sa
    session.commit()
    
    with app.test_request_context('/test-premium', headers=headers_free):
        response = app.make_response(premium_route())
    assert response.status_code == 200
    assert response.get_json()['success'] is True

def test_onboarding_atomic_flow(client, session):
    # Test the /api/saas/onboarding endpoint (transactional)
    payload = {
        "nome_fantasia": "Auto Test Store",
        "razao_social": "Auto Test Store LTDA",
        "cnpj": "12345678901234",
        "telefone": "92988887766",
        "email_estabelecimento": "test@autostore.com",
        "nome_admin": "Admin Test",
        "email_admin": "admin@autostore.com",
        "senha_admin": "SecurePass123!"
    }
    
    # We need a superadmin token to call onboarding
    from app.models import Funcionario
    from flask_jwt_extended import create_access_token
    
    superadmin = Funcionario.query.filter_by(is_super_admin=True).first()
    if not superadmin:
        # Create a temporary one if conftest doesn't provide it
        from app.models import Estabelecimento
        estab = Estabelecimento.query.first()
        superadmin = Funcionario(
            estabelecimento_id=estab.id,
            nome="Global Admin",
            username="super_test",
            email="super@test.com",
            role="admin",
            is_super_admin=True,
            cpf="00011122233",
            data_nascimento=date(1980, 1, 1),
            celular="92900000000",
            cargo="CTO",
            data_admissao=date(2024, 1, 1)
        )
        superadmin.set_password("pass")
        session.add(superadmin)
        session.commit()

    # Token espelhando o login real: super admin sempre carrega estabelecimento_id
    # e status; sem eles o guard multi-tenant (fail-closed) devolve 401.
    token = create_access_token(identity=str(superadmin.id), additional_claims={
        "is_super_admin": True,
        "estabelecimento_id": superadmin.estabelecimento_id,
        "role": "admin",
        "status": "ativo",
    })
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post('/api/saas/onboarding', json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['estabelecimento']['nome_fantasia'] == "Auto Test Store"
    
    # Verify DB state
    from app.models import Estabelecimento as Est, Funcionario as Fun
    stored_est = Est.query.filter_by(email="test@autostore.com").first()
    assert stored_est is not None
    assert stored_est.plano == "Premium" # Default in onboarding

    # Espelha tenant do NOVO estabelecimento p/ verificar seu admin (filtrado).
    from flask import g, has_request_context
    if has_request_context():
        g.estabelecimento_id = stored_est.id
    stored_admin = Fun.query.filter_by(email="admin@autostore.com").first()
    assert stored_admin is not None
    assert stored_admin.check_password("SecurePass123!") is True
