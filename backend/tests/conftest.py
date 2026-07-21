import os
import pytest

os.environ.setdefault("RESEND_API_KEY", "test-resend-key")

from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope="session")
def app():
    """ Crea la aplicación Flask configurada para testing """
    app = create_app("testing")
    with app.app_context():
        yield app

import sqlalchemy as sa

@pytest.fixture(scope="function")
def db_session(app):
    """ Crea una sesión de base de datos aislada para cada test. Usa el patrón de savepoints anidados para soportar commits internos """
    connection = _db.engine.connect()
    transaction = connection.begin()
    
    import sqlalchemy as sa
    raw_session = sa.orm.Session(bind=connection, join_transaction_mode="create_savepoint")
    
    _db.session = sa.orm.scoped_session(lambda: raw_session)

    yield _db.session
    
    _db.session.remove()
    transaction.rollback()
    connection.close()