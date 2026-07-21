import pytest
from flask_jwt_extended import create_access_token, get_csrf_token
from app.models.user import User

def _mint_token_and_csrf(user_id):
    """ Genera un token de acceso real y extrae su CSRF. Duplicado deliberadamente aqui (principio DAMP) para mantener el archivo autocontenido sin afectar los tests de revocacion previos ni crear acoplamiento artificial con ellos """
    token = create_access_token(identity=str(user_id))
    csrf = get_csrf_token(token)
    return token, csrf

def test_admin_endpoint_rejects_missing_token(client):
    """ Hacer un GET a /api/admin/users SIN ninguna cookie ni header. Verificar 401 con code == "UNAUTHORIZED" """
    response = client.get("/api/admin/users")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"

def test_admin_endpoint_rejects_insufficient_role(app, db_session, client):
    """ Crear un usuario real con role="REGISTERED". Hacer GET a /api/admin/users con ese token. Verificar 403 con code == "FORBIDDEN" """
    user = User(
        email="registered@example.com",
        first_name="Test",
        last_name="Registered",
        password_hash="dummy",
        role="REGISTERED",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user.id)
    
    client.set_cookie("access_token_cookie", token)
    response = client.get("/api/admin/users", headers={"X-CSRF-TOKEN": csrf})
    
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "FORBIDDEN"

def test_admin_endpoint_allows_sufficient_role(app, db_session, client):
    """ Crear un usuario real con role="ADMIN". Hacer GET a /api/admin/users. Verificar 200 """
    user = User(
        email="admin@example.com",
        first_name="Test",
        last_name="Admin",
        password_hash="dummy",
        role="ADMIN",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user.id)
    
    client.set_cookie("access_token_cookie", token)
    response = client.get("/api/admin/users", headers={"X-CSRF-TOKEN": csrf})
    
    assert response.status_code == 200

def test_admin_endpoint_rejects_token_for_deleted_user(app, db_session, client):
    """ Verifica que un token emitido para un usuario que luego fue eliminado de la base de datos recibe 401 UNAUTHORIZED. El token sigue siendo criptograficamente valido, pero ya no corresponde a ninguna identidad existente, por lo que el frontend debe reaccionar igual que ante un token ausente: redirigir a login """
    user = User(
        email="deleted@example.com",
        first_name="Test",
        last_name="Deleted",
        password_hash="dummy",
        role="ADMIN",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)
    
    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}
    
    db_session.delete(user)
    db_session.commit()
    
    response = client.get("/api/admin/users", headers=headers)
    
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"
