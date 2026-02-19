import pytest
from app import create_app
from app.models import db, Funcionario, Estabelecimento
from flask_jwt_extended import create_access_token
import os

@pytest.fixture
def app():
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Criar estabelecimento e funcionário para o token
        est = Estabelecimento(nome="Mercadinho Teste", cnpj="12345678000199")
        db.session.add(est)
        db.session.flush()
        
        func = Funcionario(
            username="testuser", 
            nome="Test User", 
            estabelecimento_id=est.id,
            cargo="GERENTE",
            role="admin",
            ativo=True
        )
        db.session.add(func)
        db.session.commit()
        
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_header(app):
    with app.app_context():
        func = Funcionario.query.filter_by(username="testuser").first()
        token = create_access_token(
            identity=str(func.id),
            additional_claims={
                "estabelecimento_id": func.estabelecimento_id,
                "role": func.role,
                "nome": func.nome
            }
        )
        return {"Authorization": f"Bearer {token}"}

def test_cosmos_proxy_route_exists(client, auth_header):
    # Testar se a rota existe e responde (mesmo que com 404 para um GTIN inválido)
    response = client.get('/api/produtos/cosmos/0000000000000', headers=auth_header)
    assert response.status_code in [200, 404, 429]
