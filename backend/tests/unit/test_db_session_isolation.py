import pytest
from sqlalchemy import text
from app.models.category import Category
from app.extensions import db

def test_a_write_visible_within_transaction(db_session):
    """ Test A: Escribe un registro y valida que existe DENTRO de la transacción del test. Este test se ejecuta primero por orden alfabético """
    new_category = Category(id=9999, name="TestIsolationCategory123")
    db_session.add(new_category)
    db_session.commit()
    
    # Confirma que es visible dentro de esta misma sesión
    cat = db_session.query(Category).filter_by(name="TestIsolationCategory123").first()
    assert cat is not None
    assert cat.name == "TestIsolationCategory123"

def test_b_rollback_after_test_completes(app):
    """ Test B: Abre una conexión limpia y separada SIN el fixture db_session. Comprueba que la tabla sigue limpia y el registro del test A nunca se guardó definitivamente tras el teardown del test A """
    with db.engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM categories WHERE name = 'TestIsolationCategory123'")
        ).fetchone()
        
        # Debe ser None porque la transacción de db_session ya hizo rollback al terminar test_a_write_visible_within_transaction
        assert result is None
