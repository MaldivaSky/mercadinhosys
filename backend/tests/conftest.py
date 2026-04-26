import pytest
import os
import random
import string
from datetime import date
from decimal import Decimal

# Patch environment BEFORE anything else
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AIVEN_DATABASE_URL"] = ""
os.environ["POSTGRES_URL"] = ""
os.environ["FLASK_ENV"] = "simulation" # Bypass CNPJ/CPF strict validation
os.environ["SKIP_DB_SETUP"] = "true"

from app import create_app, db
from app.models import Estabelecimento, Funcionario, Configuracao

def random_string(length=10):
    return ''.join(random.choices(string.digits, k=length))

@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": "industrial-secret-test"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def session(app):
    with app.app_context():
        # Complete clean state
        db.drop_all()
        db.create_all()
        
        # Unique data for each function-scoped test
        suffix = random_string(4)
        estab = Estabelecimento(
            nome_fantasia=f"Loja Teste {suffix}",
            razao_social=f"MercadinhoSys Test {suffix} LTDA",
            cnpj=f"1234567800{suffix}",
            email=f"teste_{suffix}@mercadinho.sys",
            telefone="92999999999",
            data_abertura=date(2024, 1, 1),
            plano="PREMIUM",
            # EnderecoMixin fields
            cep="69000-000",
            logradouro="Rua Industrial",
            numero="101",
            bairro="Distrito",
            cidade="Manaus",
            estado="AM",
            pais="Brasil"
        )
        db.session.add(estab)
        db.session.flush()

        admin = Funcionario(
            estabelecimento_id=estab.id,
            nome=f"CTO Auditor {suffix}",
            cpf=f"111222333{suffix}",
            username=f"admin_{suffix}",
            role="admin",
            ativo=True,
            # Mandatory Industrial Fields
            data_nascimento=date(1990, 1, 1),
            celular="92999999999",
            email=f"admin_{suffix}@mercadinho.sys",
            cargo="Gerente",
            data_admissao=date(2024, 1, 1),
            salario_base=Decimal("5000.00")
        )
        admin.set_password("industrial-secret")
        db.session.add(admin)

        config = Configuracao(estabelecimento_id=estab.id)
        db.session.add(config)

        db.session.commit()
        yield db.session
