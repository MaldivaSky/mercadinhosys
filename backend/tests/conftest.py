"""
Configuração do pytest para testes do MercadinhoSys
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app, db

@pytest.fixture(scope='session')
def app():
    """Cria aplicação Flask para testes"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    return app

@pytest.fixture(scope='session')
def _db(app):
    """Cria banco de dados para testes"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def session(_db):
    """Cria sessão de banco de dados para cada teste"""
    connection = _db.engine.connect()
    transaction = connection.begin()
    
    session = _db.create_scoped_session(
        options={"bind": connection, "binds": {}}
    )
    _db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()
