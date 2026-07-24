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
    
    """ Guardamos la sesion original para restaurarla al finalizar. Si no la restauramos, db.session queda apuntando a una conexion ya cerrada, lo que rompe cualquier test posterior que use db.session directamente en vez del fixture (como test_backup_restore_schema_sync) """
    original_session = _db.session
    _db.session = sa.orm.scoped_session(lambda: raw_session)

    yield _db.session
    
    _db.session.remove()
    transaction.rollback()
    connection.close()
    _db.session = original_session


@pytest.fixture(autouse=True)
def _cleanup_db_session_after_test(app):
    # No abrimos un app_context nuevo aqui; la fixture app (scope session) ya mantiene uno activo durante toda la suite. Abrir uno anidado crea un scope distinto y limpia la sesion equivocada, dejando intacta la conexion real que se abrio durante el test.
    yield
    _db.session.remove()