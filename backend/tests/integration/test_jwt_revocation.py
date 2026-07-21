import pytest
import jwt
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token, get_csrf_token, decode_token
from app.models.user import User

def _mint_token_and_csrf(user_id, custom_iat=None, secret_key=None):
    """ Genera un token de acceso real y extrae su CSRF.
    Si custom_iat se proporciona, modifica manualmente el claim 'iat' decodificando y re-encodeando con el secret_key de la app, ya que flask_jwt_extended no expone un parametro directo para fijar 'iat'.Debe ser invocado dentro del contexto de la aplicacion (app.app_context()) """
    token = create_access_token(identity=str(user_id))
    
    if custom_iat is not None and secret_key is not None:
        decoded = decode_token(token)
        decoded["iat"] = int(custom_iat.timestamp())
        token = jwt.encode(decoded, secret_key, algorithm="HS256")
        
    csrf = get_csrf_token(token)
    return token, csrf

def test_token_revoked_immediately_after_deactivation(app, db_session, client):
    """ Verifica que un token emitido para un usuario activo deja de funcionar inmediatamente despues de que ese usuario es desactivado (soft-delete), debido a que check_if_token_revoked intercepta y revoca la sesion """
    # Creamos un usuario real en la base de datos (activo por defecto)
    user = User(
        email="test_revocation@example.com",
        first_name="Test",
        last_name="Revocation",
        password_hash="dummy_hash_para_test",
        role="REGISTERED",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Generamos el token y CSRF
    with app.app_context():
        token, csrf = _mint_token_and_csrf(user.id)

    """ Configuramos el test client con la cookie y el header, los valores por defecto de flask-jwt-extended en el proyecto son:
    a. Cookie name: access_token_cookie
    b. CSRF Header: X-CSRF-TOKEN
    """
    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}

    # Hacemos un GET a /api/auth/me y verificar que responde 200 (usuario activo)
    response_active = client.get("/api/auth/me", headers=headers)
    assert response_active.status_code == 200, "El token deberia funcionar para un usuario activo."

    # Modificamos el usuario, is_active = False y guardar
    user.is_active = False
    db_session.add(user)
    db_session.commit()

    # Aplicamos OTRO GET a /api/auth/me con el MISMO client y header, sin generar token nuevo. El client ya tiene la cookie guardada desde el set_cookie anterior.
    response_revoked = client.get("/api/auth/me", headers=headers)
    assert response_revoked.status_code == 401, "El token debio ser rechazado porque el usuario esta inactivo."
    
    data = response_revoked.get_json()
    assert data["error"]["code"] == "TOKEN_REVOKED", "El error debio ser especificamente TOKEN_REVOKED segun el handler revoked_token_loader."


def test_token_revoked_after_password_change(app, db_session, client):
    """ Verifica que un token emitido ANTES de que el usuario cambie su contrasena es revocado automaticamente """
    # Creamos un usuario cuyo password_changed_at fue hace 1 hora
    past_password_change = datetime.now(timezone.utc) - timedelta(hours=1)
    user = User(
        email="test_pwd_revoked@example.com",
        first_name="Test",
        last_name="PwdRevoked",
        password_hash="dummy_hash_para_test",
        role="REGISTERED",
        is_active=True,
        password_changed_at=past_password_change
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Generamos un token emitido hace 2 horas (ANTERIOR al cambio de contrasena)
    token_issued_at = datetime.now(timezone.utc) - timedelta(hours=2)
    with app.app_context():
        secret_key = app.config["JWT_SECRET_KEY"]
        token, csrf = _mint_token_and_csrf(user.id, custom_iat=token_issued_at, secret_key=secret_key)

    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}

    # El GET debe ser 401 con TOKEN_REVOKED
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401, "El token viejo debio ser rechazado tras el cambio de contrasena."
    assert response.get_json()["error"]["code"] == "TOKEN_REVOKED"


def test_token_valid_after_password_change_if_issued_later(app, db_session, client):
    """ Verifica que un token emitido DESPUES de un cambio de contrasena es valido y no se revoca erronamente """
    # Creamos un usuario cuyo password_changed_at fue hace 2 horas
    past_password_change = datetime.now(timezone.utc) - timedelta(hours=2)
    user = User(
        email="test_pwd_valid@example.com",
        first_name="Test",
        last_name="PwdValid",
        password_hash="dummy_hash_para_test",
        role="REGISTERED",
        is_active=True,
        password_changed_at=past_password_change
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Generamos un token emitido hace 1 hora (POSTERIOR al cambio de contrasena)
    token_issued_at = datetime.now(timezone.utc) - timedelta(hours=1)
    with app.app_context():
        secret_key = app.config["JWT_SECRET_KEY"]
        token, csrf = _mint_token_and_csrf(user.id, custom_iat=token_issued_at, secret_key=secret_key)

    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}

    # El GET debe ser 200 (token valido)
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200, "El token nuevo debio ser aceptado."


def test_oauth_only_user_never_revoked_by_password_change(app, db_session, client):
    """ Verifica que un usuario exclusivamente OAuth (password_changed_at=None) nunca tiene sus tokens revocados por este mecanismo, sin importar el IAT """
    # Creamos un usuario sin contrasena propia (simulando OAuth puro)
    user = User(
        email="test_oauth_only@example.com",
        first_name="Test",
        last_name="OAuth",
        password_hash=None,
        password_changed_at=None,
        role="REGISTERED",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Generamos un token normal (iat actual)
    with app.app_context():
        token, csrf = _mint_token_and_csrf(user.id)

    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}

    # El GET debe ser 200 (token valido)
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200, "El token del usuario OAuth debio ser aceptado."
