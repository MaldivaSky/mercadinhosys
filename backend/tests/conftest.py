"""
Configuração do pytest para testes de integração do MercadinhoSys.
Utiliza a DATABASE_URL da Aiven configurada no .env.
Cada teste roda dentro de uma transação com SAVEPOINT + rollback,
garantindo que o banco Aiven não seja poluído.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app import create_app, db as _db
from app.models import Funcionario, Estabelecimento
from flask_jwt_extended import create_access_token


def _get_cloud_url():
    return (
        os.environ.get("AIVEN_DATABASE_URL")
        or os.environ.get("NEON_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )


@pytest.fixture(scope="session")
def app():
    db_url = _get_cloud_url()
    if not db_url:
        pytest.skip("Nenhuma DATABASE_URL cloud configurada.")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    os.environ["AIVEN_DATABASE_URL"] = db_url

    app = create_app("default")
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": db_url,
        "SERVER_NAME": "localhost",
        "PREFERRED_URL_SCHEME": "http",
    })

    with app.app_context():
        _db.create_all()

    yield app


@pytest.fixture(autouse=True)
def _rollback_after_test(app):
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        nested = connection.begin_nested()

        old_session = _db.session
        session_factory = _db.sessionmaker(bind=connection)
        session = _db.scoped_session(session_factory)
        _db.session = session

        @_db.event.listens_for(session, "after_transaction_end")
        def restart_savepoint(s, trans):
            nonlocal nested
            if trans.nested and not trans._parent.nested:
                nested = connection.begin_nested()

        yield session

        _db.session = old_session
        session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def admin_func(app):
    with app.app_context():
        admin = Funcionario.query.filter_by(username="admin").first()
        if not admin:
            pytest.skip("Funcionário admin não encontrado. Rode o seed.")
        return {
            "id": admin.id,
            "username": admin.username,
            "nome": admin.nome,
            "estabelecimento_id": admin.estabelecimento_id,
            "role": admin.role,
            "cargo": admin.cargo,
            "status": getattr(admin, "status", "ativo"),
        }


@pytest.fixture(scope="session")
def auth_headers(app, admin_func):
    with app.app_context():
        est = Estabelecimento.query.get(admin_func["estabelecimento_id"])
        token = create_access_token(
            identity=str(admin_func["id"]),
            additional_claims={
                "username": admin_func["username"],
                "nome": admin_func["nome"],
                "estabelecimento_id": admin_func["estabelecimento_id"],
                "estabelecimento_nome": est.nome_fantasia if est else "",
                "status": admin_func["status"],
                "role": admin_func["role"],
                "cargo": admin_func["cargo"],
            },
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }


@pytest.fixture(scope="session")
def estabelecimento_id(admin_func):
    return admin_func["estabelecimento_id"]
