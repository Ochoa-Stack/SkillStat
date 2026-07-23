import pytest

""" test_backup_restore_schema_sync invoca pg_restore, que destruye y reemplaza la base de datos completa. Esto deja la conexion SQLAlchemy del fixture db_session (scope="session") en un estado invalido (ResourceClosedError) para cualquier test que corra despues en la misma sesion de pytest. Por eso forzamos que ese modulo sea el ultimo en ejecutarse dentro de integration """
def pytest_collection_modifyitems(items):
    LAST_MODULE = "test_backup_restore_schema_sync"
    regular = [i for i in items if LAST_MODULE not in i.nodeid]
    deferred = [i for i in items if LAST_MODULE in i.nodeid]
    items[:] = regular + deferred
