from datetime import datetime, timezone

import pytest
from app.models.user import User
from app.utils.hash import hash_password


# Helpers - duplicados localmente (principio DAMP: cada archivo de tests es autocontenido). Si la suite crece significativamente, extraer a tests/helpers.py queda como decision pendiente.

_VALID_PASSWORD = "Secure1!"


def _make_user(db_session, email="user@example.com", password=_VALID_PASSWORD,
               verified=True, role="REGISTERED"):
    """ Crea un usuario directamente en BD con todos los campos necesarios. Si verified=True setea email_verified_at, de lo contrario lo deja en None """
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        password_hash=hash_password(password) if password else None,
        role=role,
        is_active=True,
        email_verified_at=datetime.now(timezone.utc) if verified else None,
        password_changed_at=datetime.now(timezone.utc) if password else None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _register_payload(email="new@example.com", password=_VALID_PASSWORD,
                      first_name="Test", last_name="User"):
    return {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
    }


# Tests: POST /api/auth/register

def test_register_success(app, db_session, client, monkeypatch):
    """ POST con payload valido. El correo de verificacion se mockea. Verificar 201, usuario en BD con password hasheado, role REGISTERED, password_changed_at no nulo, y email_verified_at nulo (pendiente) """
    mock_calls = []

    def fake_send(to_email, token):
        mock_calls.append((to_email, token))

    monkeypatch.setattr(
        "app.services.email_service.send_verification_email", fake_send
    )

    payload = _register_payload(email="register_ok@example.com")
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    data = response.get_json()
    assert "message" in data["data"]

    # Verificar el usuario en BD
    from app.models.user import User as UserModel
    from app.extensions import db
    persisted = db.session.query(UserModel).filter_by(email="register_ok@example.com").first()
    assert persisted is not None
    # Contraseña nunca en texto plano
    assert persisted.password_hash != _VALID_PASSWORD
    # La contraseña esta hasheada con bcrypt (empieza con $2b$)
    assert persisted.password_hash.startswith("$2b$")
    assert persisted.role == "REGISTERED"
    assert persisted.password_changed_at is not None
    assert persisted.email_verified_at is None

    # El mock fue invocado exactamente una vez
    assert len(mock_calls) == 1
    assert mock_calls[0][0] == "register_ok@example.com"


def test_register_duplicate_email_returns_409(app, db_session, client, monkeypatch):
    """ Crear un usuario existente, luego registrar con el mismo email. Verificar 409 con code CONFLICT """
    monkeypatch.setattr(
        "app.services.email_service.send_verification_email", lambda *a: None
    )

    email = "duplicate@example.com"
    _make_user(db_session, email=email)

    payload = _register_payload(email=email)
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "CONFLICT"


def test_register_invalid_payload_returns_422(app, client):
    """ POST con payload incompleto — sin email. Verificar 422 VALIDATION_ERROR. No necesita db_session porque el schema rechaza antes de tocar la BD """
    payload = {"password": _VALID_PASSWORD, "first_name": "Test", "last_name": "User"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_succeeds_even_if_email_delivery_fails(app, db_session, client, monkeypatch):
    """ Mockear send_verification_email para que lance EmailDeliveryError. El registro NO se revierte: la respuesta sigue siendo 201, pero con el mensaje alternativo, y el usuario quedo en BD """
    from app.services.email_service import EmailDeliveryError

    def fake_send_fail(to_email, token):
        raise EmailDeliveryError("Servicio de correo caido")

    monkeypatch.setattr(
        "app.services.email_service.send_verification_email", fake_send_fail
    )

    email = "delivery_fail@example.com"
    payload = _register_payload(email=email)
    response = client.post("/api/auth/register", json=payload)

    # El registro no se revierte aunque el correo falle
    assert response.status_code == 201
    data = response.get_json()
    # El mensaje de respuesta es distinto al caso exitoso
    assert "no pudimos enviar el correo" in data["data"]["message"].lower()

    # El usuario si quedo creado en BD
    from app.models.user import User as UserModel
    from app.extensions import db
    persisted = db.session.query(UserModel).filter_by(email=email).first()
    assert persisted is not None


# Tests: POST /api/auth/login

def test_login_success(app, db_session, client):
    """ Usuario verificado con credenciales correctas. Verificar 200 y que la cookie de acceso quedo seteada en la respuesta """
    email = "login_ok@example.com"
    password = _VALID_PASSWORD
    _make_user(db_session, email=email, password=password, verified=True)

    response = client.post("/api/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200
    # El token viaja solo en cookie, nunca en el cuerpo
    data = response.get_json()
    assert "data" in data

    # La cookie de acceso debe haberse seteado en la respuesta. set_access_cookies de flask-jwt-extended escribe 'access_token_cookie'. Werkzeug moderno expone get_cookie(name); retorna None si no existe.
    cookie = client.get_cookie("access_token_cookie")
    assert cookie is not None, "La cookie 'access_token_cookie' no fue seteada tras un login exitoso"


def test_login_wrong_password_returns_401(app, db_session, client):
    """ Usuario real con password correcto en BD. POST con password incorrecto. Verificar 401 UNAUTHORIZED (mismo code que email inexistente, sin distincion que permita enumeracion de cuentas) """
    email = "wrong_pass@example.com"
    _make_user(db_session, email=email, password=_VALID_PASSWORD, verified=True)

    response = client.post(
        "/api/auth/login", json={"email": email, "password": "WrongPass999!"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_login_nonexistent_email_returns_401(app, client):
    """ POST con email que no existe en BD. Verificar 401 UNAUTHORIZED. El code debe ser identico al de password incorrecto; sin distincion para evitar enumeracion de cuentas """
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": _VALID_PASSWORD},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_login_unverified_email_returns_403(app, db_session, client):
    """ Usuario con credenciales correctas pero email_verified_at=None. Verificar 403 EMAIL_NOT_VERIFIED """
    email = "unverified@example.com"
    password = _VALID_PASSWORD
    _make_user(db_session, email=email, password=password, verified=False)

    response = client.post("/api/auth/login", json={"email": email, "password": password})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


# Tests: POST /api/auth/google

def test_google_login_creates_new_user(app, db_session, client, monkeypatch):
    """ Google verify retorna dict valido. POST a /api/auth/google. Verificar 200, cookie seteada, usuario creado sin password_hash y con OAuthAccount vinculada """
    def fake_verify(*args, **kwargs):
        return {
            "sub": "google_uid_123",
            "email": "newgoogle@example.com",
            "email_verified": "true",
            "given_name": "Nueva",
            "family_name": "Cuenta"
        }
    monkeypatch.setattr("app.controllers.auth_bp.google_id_token.verify_oauth2_token", fake_verify)

    response = client.post("/api/auth/google", json={"credential": "fake_token"})
    assert response.status_code == 200
    
    # Cookie seteada
    cookie = client.get_cookie("access_token_cookie")
    assert cookie is not None
    
    # Verificar BD
    from app.models.user import User as UserModel
    from app.models.oauth_account import OAuthAccount
    from app.extensions import db
    
    persisted = db.session.query(UserModel).filter_by(email="newgoogle@example.com").first()
    assert persisted is not None
    assert persisted.password_hash is None
    assert persisted.email_verified_at is not None
    assert persisted.first_name == "Nueva"
    assert persisted.last_name == "Cuenta"
    
    oauth_acc = db.session.query(OAuthAccount).filter_by(user_id=persisted.id, provider="google", provider_user_id="google_uid_123").first()
    assert oauth_acc is not None


def test_google_login_existing_oauth_account(app, db_session, client, monkeypatch):
    """ Usuario y OAuthAccount ya existen. Retorna el mismo sub. Verificar 200 y que no se duplica el usuario """
    email = "existing_oauth@example.com"
    user = _make_user(db_session, email=email, password=None, verified=True)
    
    from app.models.oauth_account import OAuthAccount
    oauth_acc = OAuthAccount(user_id=user.id, provider="google", provider_user_id="existing_sub_456")
    db_session.add(oauth_acc)
    db_session.commit()
    
    original_user_id = user.id

    def fake_verify(*args, **kwargs):
        return {
            "sub": "existing_sub_456",
            "email": email,
            "email_verified": "true",
            "given_name": "Existing",
            "family_name": "User"
        }
    monkeypatch.setattr("app.controllers.auth_bp.google_id_token.verify_oauth2_token", fake_verify)

    response = client.post("/api/auth/google", json={"credential": "fake_token"})
    assert response.status_code == 200
    
    from app.models.user import User as UserModel
    from app.extensions import db
    users = db.session.query(UserModel).filter_by(email=email).all()
    assert len(users) == 1
    assert users[0].id == original_user_id


def test_google_login_links_existing_email_without_oauth(app, db_session, client, monkeypatch):
    """ Usuario registrado normal (con password) hace login con Google (mismo email). Verificar 200, usuario no duplicado, OAuthAccount creada """
    email = "link_oauth@example.com"
    user = _make_user(db_session, email=email, password=_VALID_PASSWORD, verified=True)
    original_user_id = user.id

    def fake_verify(*args, **kwargs):
        return {
            "sub": "new_sub_789",
            "email": email,
            "email_verified": "true",
            "given_name": "Linked",
            "family_name": "User"
        }
    monkeypatch.setattr("app.controllers.auth_bp.google_id_token.verify_oauth2_token", fake_verify)

    response = client.post("/api/auth/google", json={"credential": "fake_token"})
    assert response.status_code == 200
    
    from app.models.user import User as UserModel
    from app.models.oauth_account import OAuthAccount
    from app.extensions import db
    
    users = db.session.query(UserModel).filter_by(email=email).all()
    assert len(users) == 1
    assert users[0].id == original_user_id
    
    oauth_acc = db.session.query(OAuthAccount).filter_by(user_id=original_user_id, provider="google", provider_user_id="new_sub_789").first()
    assert oauth_acc is not None


def test_google_login_rejects_invalid_token(app, client, monkeypatch):
    """ Token invalido lanza ValueError desde la libreria de Google. Verificar 401 TOKEN_INVALID """
    def fake_verify_raises(*args, **kwargs):
        raise ValueError("Invalid token")
    monkeypatch.setattr("app.controllers.auth_bp.google_id_token.verify_oauth2_token", fake_verify_raises)

    response = client.post("/api/auth/google", json={"credential": "bad_token"})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "TOKEN_INVALID"


def test_google_login_rejects_unverified_email(app, client, monkeypatch):
    """ Google dice email_verified='false'. Verificar 401 EMAIL_NOT_VERIFIED """
    def fake_verify_unverified(*args, **kwargs):
        return {
            "sub": "sub_999",
            "email": "unverified@example.com",
            "email_verified": "false",
            "given_name": "Unverified",
            "family_name": "User"
        }
    monkeypatch.setattr("app.controllers.auth_bp.google_id_token.verify_oauth2_token", fake_verify_unverified)

    response = client.post("/api/auth/google", json={"credential": "fake_token"})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


# Helpers y Tests: GET/POST /api/auth/verify-email & POST /api/auth/resend-verification

import hashlib
from datetime import timedelta
from app.models.email_verification_token import EmailVerificationToken


def _create_token(db_session, user_id, token_plain, expired=False, used=False):
    token_hash = hashlib.sha256(token_plain.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    expires_at = now - timedelta(hours=1) if expired else now + timedelta(hours=24)
    used_at = now if used else None
    evt = EmailVerificationToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=used_at
    )
    db_session.add(evt)
    db_session.commit()
    return evt


def test_verify_email_get_valid_token(app, db_session, client):
    """ GET con token valido. Verificar 200, valid=true, sin mutaciones. """
    user = _make_user(db_session, verified=False)
    token_plain = "valid_token_123"
    evt = _create_token(db_session, user.id, token_plain)

    response = client.get(f"/api/auth/verify-email?token={token_plain}")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["data"]["valid"] is True
    
    # Comprobar que no hay side-effects
    db_session.refresh(evt)
    db_session.refresh(user)
    assert evt.used_at is None
    assert user.email_verified_at is None


def test_verify_email_get_invalid_token_returns_404(app, client):
    """ GET con token inexistente. Verificar 404 TOKEN_INVALID. """
    response = client.get("/api/auth/verify-email?token=does_not_exist")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "TOKEN_INVALID"


def test_verify_email_get_expired_token_returns_410(app, db_session, client):
    """ GET con token expirado. Verificar 410 TOKEN_EXPIRED. """
    user = _make_user(db_session, verified=False)
    token_plain = "expired_token_123"
    _create_token(db_session, user.id, token_plain, expired=True)

    response = client.get(f"/api/auth/verify-email?token={token_plain}")
    assert response.status_code == 410
    assert response.get_json()["error"]["code"] == "TOKEN_EXPIRED"


def test_verify_email_post_marks_verified(app, db_session, client):
    """ POST con token valido. Verificar 200 y que el usuario y token se mutan. """
    user = _make_user(db_session, verified=False)
    token_plain = "valid_post_token_123"
    evt = _create_token(db_session, user.id, token_plain)

    response = client.post("/api/auth/verify-email", json={"token": token_plain})
    
    assert response.status_code == 200
    
    db_session.refresh(evt)
    db_session.refresh(user)
    assert evt.used_at is not None
    assert user.email_verified_at is not None


def test_verify_email_post_already_used_returns_409(app, db_session, client):
    """ POST con token ya usado. Verificar 409 TOKEN_ALREADY_USED. """
    user = _make_user(db_session, verified=False)
    token_plain = "used_token_123"
    _create_token(db_session, user.id, token_plain, used=True)

    response = client.post("/api/auth/verify-email", json={"token": token_plain})
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "TOKEN_ALREADY_USED"


def test_resend_verification_unknown_email_returns_generic_200(app, client, monkeypatch):
    """ Resend a email no existente. Verificar 200 para evitar enumeracion. """
    mock_calls = []
    monkeypatch.setattr("app.services.email_service.send_verification_email", lambda to, t: mock_calls.append((to, t)))
    
    response = client.post("/api/auth/resend-verification", json={"email": "nobody@example.com"})
    assert response.status_code == 200
    assert "nuevo enlace" in response.get_json()["data"]["message"].lower()
    assert len(mock_calls) == 0


def test_resend_verification_already_verified_returns_generic_200(app, db_session, client, monkeypatch):
    """ Resend a email ya verificado. Verificar 200 pero sin email real. """
    user = _make_user(db_session, email="already_verified@example.com", verified=True)
    
    mock_calls = []
    monkeypatch.setattr("app.services.email_service.send_verification_email", lambda to, t: mock_calls.append((to, t)))
    
    response = client.post("/api/auth/resend-verification", json={"email": user.email})
    assert response.status_code == 200
    
    from app.extensions import db
    count = db.session.query(EmailVerificationToken).filter_by(user_id=user.id).count()
    assert count == 0
    assert len(mock_calls) == 0


def test_resend_verification_creates_new_token(app, db_session, client, monkeypatch):
    """ Resend a email no verificado. Verificar 200, token creado en BD, y llamada de correo. """
    user = _make_user(db_session, email="needs_resend@example.com", verified=False)
    
    mock_calls = []
    monkeypatch.setattr("app.services.email_service.send_verification_email", lambda to, t: mock_calls.append((to, t)))
    
    response = client.post("/api/auth/resend-verification", json={"email": user.email})
    assert response.status_code == 200
    
    from app.extensions import db
    count = db.session.query(EmailVerificationToken).filter_by(user_id=user.id).count()
    assert count == 1
    assert len(mock_calls) == 1
    assert mock_calls[0][0] == user.email


# Helpers y Tests: GET /api/auth/me, POST /api/auth/forgot-password, POST /api/auth/reset-password

from app.models.password_reset_token import PasswordResetToken


def _create_pwd_reset_token(db_session, user_id, token_plain, expired=False, used=False):
    token_hash = hashlib.sha256(token_plain.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    expires_at = now - timedelta(hours=1) if expired else now + timedelta(hours=24)
    used_at = now if used else None
    evt = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=used_at
    )
    db_session.add(evt)
    db_session.commit()
    return evt


def test_forgot_password_unknown_email_returns_generic_200(app, client, monkeypatch):
    mock_calls = []
    monkeypatch.setattr("app.services.email_service.send_password_reset_email", lambda to, t: mock_calls.append((to, t)))
    
    response = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert response.status_code == 200
    assert len(mock_calls) == 0


def test_forgot_password_known_email_creates_token_and_sends_email(app, db_session, client, monkeypatch):
    user = _make_user(db_session, email="known_forgot@example.com")
    
    mock_calls = []
    monkeypatch.setattr("app.services.email_service.send_password_reset_email", lambda to, t: mock_calls.append((to, t)))
    
    response = client.post("/api/auth/forgot-password", json={"email": user.email})
    assert response.status_code == 200
    
    from app.extensions import db
    count = db.session.query(PasswordResetToken).filter_by(user_id=user.id).count()
    assert count == 1
    assert len(mock_calls) == 1
    assert mock_calls[0][0] == user.email


def test_reset_password_success(app, db_session, client):
    user = _make_user(db_session, email="reset_ok@example.com", password=_VALID_PASSWORD)
    original_hash = user.password_hash
    original_changed_at = user.password_changed_at
    
    token_plain = "valid_pwd_reset_token_123"
    prt = _create_pwd_reset_token(db_session, user.id, token_plain)

    response = client.post("/api/auth/reset-password", json={"token": token_plain, "new_password": "NewSecure1!"})
    assert response.status_code == 200
    
    db_session.refresh(prt)
    db_session.refresh(user)
    assert prt.used_at is not None
    assert user.password_hash != original_hash
    assert user.password_changed_at > original_changed_at


def test_reset_password_invalidates_old_tokens(app, db_session, client):
    user = _make_user(db_session, email="reset_revoke@example.com", password=_VALID_PASSWORD)
    user.password_changed_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    from flask_jwt_extended import create_access_token, get_csrf_token, decode_token
    import jwt
    with app.app_context():
        token = create_access_token(identity=str(user.id))
        
        # Retroceder el iat 1 hora para asegurar que es estrictamente menor al nuevo password_changed_at pero mayor al password_changed_at original
        token_issued_at = datetime.now(timezone.utc) - timedelta(hours=1)
        decoded = decode_token(token)
        decoded["iat"] = int(token_issued_at.timestamp())
        token = jwt.encode(decoded, app.config["JWT_SECRET_KEY"], algorithm="HS256")
        
        csrf = get_csrf_token(token)

    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}

    # Verify token works BEFORE reset
    resp_before = client.get("/api/auth/me", headers=headers)
    assert resp_before.status_code == 200

    token_plain = "revoke_reset_token_123"
    _create_pwd_reset_token(db_session, user.id, token_plain)

    # Do the reset using endpoint
    resp_reset = client.post("/api/auth/reset-password", json={"token": token_plain, "new_password": "NewSecure1!"})
    assert resp_reset.status_code == 200

    # Verify old token NO LONGER works (TOKEN_REVOKED)
    resp_after = client.get("/api/auth/me", headers=headers)
    assert resp_after.status_code == 401
    assert resp_after.get_json()["error"]["code"] == "TOKEN_REVOKED"


def test_reset_password_invalid_or_expired_token_returns_400(app, db_session, client):
    response = client.post("/api/auth/reset-password", json={"token": "does_not_exist", "new_password": "NewSecure1!"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_TOKEN"


def test_get_me_success(app, db_session, client):
    user = _make_user(db_session, email="get_me_ok@example.com")
    
    from flask_jwt_extended import create_access_token, get_csrf_token
    with app.app_context():
        token = create_access_token(identity=str(user.id))
        csrf = get_csrf_token(token)

    client.set_cookie("access_token_cookie", token)
    headers = {"X-CSRF-TOKEN": csrf}

    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.get_json()["data"]
    assert data["email"] == "get_me_ok@example.com"
    assert data["first_name"] == "Test"
    assert data["role"] == "REGISTERED"


def test_get_me_without_token_returns_401(app, client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401