import pytest
from flask_jwt_extended import create_access_token, get_csrf_token
from app.models.user import User

def _mint_token_and_csrf(user_id):
    """ Genera un token de acceso real y extrae su CSRF. Duplicado deliberadamente aqui (principio DAMP) para mantener el archivo autocontenido sin afectar los tests previos ni crear acoplamiento artificial """
    token = create_access_token(identity=str(user_id))
    csrf = get_csrf_token(token)
    return token, csrf

def test_last_admin_cannot_demote_self(app, db_session, client):
    """ Verifica que el unico administrador activo no puede quitarse el rol de ADMIN """
    user = User(
        email="only_admin_role@example.com",
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
    headers = {"X-CSRF-TOKEN": csrf}
    
    response = client.patch(f"/api/admin/users/{user.id}/role", json={"role": "REGISTERED"}, headers=headers)
    
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "LAST_ADMIN_PROTECTED"
    
    updated_user = db_session.get(User, user.id)
    assert updated_user.role == "ADMIN", "La operacion no debio mutar el rol del usuario."

def test_last_admin_cannot_deactivate_self(app, db_session, client):
    """ Verifica que el unico administrador activo no puede desactivar su propia cuenta """
    user = User(
        email="only_admin_status@example.com",
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
    headers = {"X-CSRF-TOKEN": csrf}
    
    response = client.patch(f"/api/admin/users/{user.id}/status", json={"is_active": False}, headers=headers)
    
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "LAST_ADMIN_PROTECTED"
    
    updated_user = db_session.get(User, user.id)
    assert updated_user.is_active is True, "La operacion no debio mutar el status del usuario."

def test_admin_can_demote_self_if_another_admin_active(app, db_session, client):
    """ Verifica que un administrador si puede quitarse el rol si existe al menos otro administrador activo en el sistema """
    user1 = User(
        email="admin1_self_demote@example.com",
        first_name="Admin",
        last_name="One",
        password_hash="dummy",
        role="ADMIN",
        is_active=True
    )
    user2 = User(
        email="admin2_active@example.com",
        first_name="Admin",
        last_name="Two",
        password_hash="dummy",
        role="ADMIN",
        is_active=True
    )
    db_session.add_all([user1, user2])
    db_session.commit()
    db_session.refresh(user1)
    
    with app.app_context():
        token, csrf = _mint_token_and_csrf(user1.id)
    
    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}
    
    response = client.patch(f"/api/admin/users/{user1.id}/role", json={"role": "REGISTERED"}, headers=headers)
    
    assert response.status_code == 200
    updated_user = db_session.get(User, user1.id)
    assert updated_user.role == "REGISTERED", "El rol debio cambiar a REGISTERED."

def test_admin_can_demote_another_admin_even_if_last_active(app, db_session, client):
    """ Verifica y documenta una asimetria del diseño actual, la proteccion de ultimo admin solo aplica para la auto-modificacion. Si el actor modifica a un tercero, la proteccion no aplica, incluso si eso dejara tecnicamente a un unico admin (o cero admins) si no hay mas activos. En este test, el actor degrada al target y la operacion procede (200 OK) """
    user_actor = User(
        email="admin_actor@example.com",
        first_name="Actor",
        last_name="Admin",
        password_hash="dummy",
        role="ADMIN",
        is_active=True
    )
    user_target = User(
        email="admin_target@example.com",
        first_name="Target",
        last_name="Admin",
        password_hash="dummy",
        role="ADMIN",
        is_active=True
    )
    db_session.add_all([user_actor, user_target])
    db_session.commit()
    db_session.refresh(user_actor)
    db_session.refresh(user_target)
    
    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_actor.id)
    
    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}
    
    response = client.patch(f"/api/admin/users/{user_target.id}/role", json={"role": "REGISTERED"}, headers=headers)
    
    assert response.status_code == 200
    updated_user_target = db_session.get(User, user_target.id)
    assert updated_user_target.role == "REGISTERED", "El rol del target debio cambiar a REGISTERED sin importar el limite de admins."
