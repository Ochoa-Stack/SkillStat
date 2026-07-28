import pytest
from flask_jwt_extended import create_access_token, get_csrf_token

from app.models.user import User
from app.models.skill import Skill
from app.models.category import Category
from app.models.alert import Alert


# Helpers de autenticacion y creacion de entidades.
# Duplicados deliberadamente aqui (principio DAMP): cada archivo de tests es autocontenido. Importar desde test_alerts_service.py crearía acoplamiento entre archivos de tests y violaría el aislamiento que DAMP busca preservar. Si en el futuro la suite crece lo suficiente como para que la duplicacion sea un problema de mantenimiento real, se puede extraer a un modulo tests/helpers.py; esa decision queda pendiente.

def _mint_token_and_csrf(user_id):
    """ Genera un token de acceso real y extrae su CSRF. Debe invocarse dentro del contexto de la aplicacion (app.app_context()) """
    token = create_access_token(identity=str(user_id))
    csrf = get_csrf_token(token)
    return token, csrf


def _make_category(db_session, name="Programacion"):
    cat = Category(name=name)
    db_session.add(cat)
    db_session.flush()
    return cat


def _make_skill(db_session, category_id, name="Python"):
    skill = Skill(name=name, canonical_name=name.lower(), category_id=category_id)
    db_session.add(skill)
    db_session.flush()
    return skill


def _make_user(db_session, email="user@example.com"):
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        password_hash="dummy",
        role="REGISTERED",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_alert(db_session, user_id, skill_id, alert_type="ABSOLUTE",
                threshold_value=50, threshold_percentage=None, active=True):
    alert = Alert(
        user_id=user_id,
        skill_id=skill_id,
        alert_type=alert_type,
        threshold_value=threshold_value,
        threshold_percentage=threshold_percentage,
        active=active,
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


# Tests: POST /api/alerts/

def test_create_alert_success(app, db_session, client):
    """ POST a /api/alerts/ con payload ABSOLUTE valido. Verificar 201 y que la alerta queda en BD con user_id del token autenticado """
    cat = _make_category(db_session, name="Cat_Create")
    skill = _make_skill(db_session, cat.id, name="Skill_Create")
    user = _make_user(db_session, email="create_ok@example.com")
    # Capturamos IDs como escalares antes del request para evitar DetachedInstanceError: el request cycle del Flask test client expira las instancias ORM de la sesion.
    skill_id = skill.id
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    payload = {"skill_id": skill_id, "alert_type": "ABSOLUTE", "threshold_value": 100}
    response = client.post("/api/alerts/", json=payload, headers={"X-CSRF-TOKEN": csrf})

    assert response.status_code == 201
    data = response.get_json()
    assert data["data"]["skill_id"] == skill_id
    assert data["data"]["alert_type"] == "ABSOLUTE"

    # Verificamos en BD que el user_id persisted es el del token, no cualquier valor externo.
    alert_id = data["data"]["id"]
    persisted = db_session.get(Alert, alert_id)
    assert persisted is not None
    assert persisted.user_id == user_id
    assert persisted.threshold_value == 100


def test_create_alert_rejects_spoofed_user_id_with_422(app, db_session, client):
    """ Marshmallow 3 usa Unknown=RAISE por defecto: si el payload incluye un campo no declarado en AlertRequestSchema (como user_id), el schema lo rechazacon ValidationError antes de que el endpoint ejecute ninguna logica. Esto protege contra asignacion cruzada de forma mas robusta aun que sobreescribir el campo post-validacion: el atacante recibe 422 y la alerta nunca llega a crearse. Verificamos ese comportamiento real """
    cat = _make_category(db_session, name="Cat_Spoof")
    skill = _make_skill(db_session, cat.id, name="Skill_Spoof")
    user = _make_user(db_session, email="spoof@example.com")
    skill_id = skill.id
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    # Incluimos user_id=99999 en el payload como intento de asignacion cruzada.
    payload = {
        "skill_id": skill_id,
        "alert_type": "ABSOLUTE",
        "threshold_value": 50,
        "user_id": 99999,
    }
    response = client.post("/api/alerts/", json=payload, headers={"X-CSRF-TOKEN": csrf})

    # Marshmallow 3 rechaza el campo desconocido con 422 VALIDATION_ERROR. El endpoint nunca crea la alerta, lo que protege contra asignacion cruzada.
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"



def test_create_alert_invalid_payload_returns_422(app, db_session, client):
    """ POST con payload invalido: ABSOLUTE sin threshold_value. Verificar 422 con code VALIDATION_ERROR, tal como el schema lo define """
    user = _make_user(db_session, email="invalid_payload@example.com")

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user.id)

    client.set_cookie("access_token_cookie", token)
    # ABSOLUTE requiere threshold_value, que aqui se omite deliberadamente.
    payload = {"skill_id": 1, "alert_type": "ABSOLUTE"}
    response = client.post("/api/alerts/", json=payload, headers={"X-CSRF-TOKEN": csrf})

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


# Tests: GET /api/alerts/

def test_get_alerts_returns_only_own_alerts(app, db_session, client):
    """ Dos usuarios con alertas propias. El primero autentica. GET /api/alerts/ debe retornar SOLO sus alertas, nunca las del segundo usuario """
    cat = _make_category(db_session, name="Cat_Get")
    skill = _make_skill(db_session, cat.id, name="Skill_Get")
    skill_id = skill.id

    user1 = _make_user(db_session, email="get_user1@example.com")
    user2 = _make_user(db_session, email="get_user2@example.com")
    user1_id = user1.id

    alert1 = _make_alert(db_session, user1_id, skill_id, threshold_value=10)
    alert2 = _make_alert(db_session, user2.id, skill_id, threshold_value=20)
    alert1_id = alert1.id
    alert2_id = alert2.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user1_id)

    client.set_cookie("access_token_cookie", token)
    response = client.get("/api/alerts/", headers={"X-CSRF-TOKEN": csrf})

    assert response.status_code == 200
    returned_ids = {a["id"] for a in response.get_json()["data"]}
    assert alert1_id in returned_ids
    assert alert2_id not in returned_ids


# Tests: DELETE /api/alerts/<id>

def test_delete_alert_success(app, db_session, client):
    """ DELETE a la alerta propia. Verificar 200 y que la alerta ya no existe en BD tras la operacion """
    cat = _make_category(db_session, name="Cat_Del")
    skill = _make_skill(db_session, cat.id, name="Skill_Del")
    user = _make_user(db_session, email="delete_ok@example.com")
    alert = _make_alert(db_session, user.id, skill.id)
    user_id = user.id
    alert_id = alert.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    response = client.delete(
        f"/api/alerts/{alert_id}", headers={"X-CSRF-TOKEN": csrf}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["deleted"] is True

    # Verificamos en BD que la alerta ya no existe.
    db_session.expire_all()
    persisted = db_session.get(Alert, alert_id)
    assert persisted is None


def test_delete_alert_not_owned_returns_404(app, db_session, client):
    """ Dos usuarios. El segundo tiene una alerta. El primero intenta DELETE sobre esa alerta. Debe recibir 404 (no 403), y la alerta del segundo debe seguir existiendo en BD """
    cat = _make_category(db_session, name="Cat_NotOwned")
    skill = _make_skill(db_session, cat.id, name="Skill_NotOwned")
    skill_id = skill.id

    user1 = _make_user(db_session, email="not_owned_u1@example.com")
    user2 = _make_user(db_session, email="not_owned_u2@example.com")
    user1_id = user1.id
    alert_of_user2 = _make_alert(db_session, user2.id, skill_id)
    alert_of_user2_id = alert_of_user2.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user1_id)

    client.set_cookie("access_token_cookie", token)
    response = client.delete(
        f"/api/alerts/{alert_of_user2_id}", headers={"X-CSRF-TOKEN": csrf}
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"

    # La alerta del usuario 2 debe seguir intacta en BD.
    db_session.expire_all()
    still_exists = db_session.get(Alert, alert_of_user2_id)
    assert still_exists is not None


def test_delete_alert_nonexistent_returns_404(app, db_session, client):
    """ DELETE a un ID que no existe en absoluto. Debe retornar 404 """
    user = _make_user(db_session, email="del_nonexist@example.com")
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    response = client.delete("/api/alerts/999999", headers={"X-CSRF-TOKEN": csrf})

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


# Tests: PATCH /api/alerts/<id>/status

def test_deactivate_alert_success(app, db_session, client):
    """ Usuario con una alerta propia, active=True. PATCH con active=False. Verificar 200 y en BD active=False """
    cat = _make_category(db_session, name="Cat_Deactivate")
    skill = _make_skill(db_session, cat.id, name="Skill_Deactivate")
    user = _make_user(db_session, email="deactivate_ok@example.com")
    alert = _make_alert(db_session, user.id, skill.id, active=True)
    alert_id = alert.id
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    response = client.patch(
        f"/api/alerts/{alert_id}/status",
        json={"active": False},
        headers={"X-CSRF-TOKEN": csrf}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["active"] is False

    db_session.expire_all()
    persisted = db_session.get(Alert, alert_id)
    assert persisted.active is False


def test_reactivate_alert_success(app, db_session, client):
    """ Usuario con alerta ya desactivada. PATCH con active=True. Verificar 200 y en BD active=True """
    cat = _make_category(db_session, name="Cat_Reactivate")
    skill = _make_skill(db_session, cat.id, name="Skill_Reactivate")
    user = _make_user(db_session, email="reactivate_ok@example.com")
    alert = _make_alert(db_session, user.id, skill.id, active=False)
    alert_id = alert.id
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    response = client.patch(
        f"/api/alerts/{alert_id}/status",
        json={"active": True},
        headers={"X-CSRF-TOKEN": csrf}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["active"] is True

    db_session.expire_all()
    persisted = db_session.get(Alert, alert_id)
    assert persisted.active is True


def test_update_status_missing_active_field_returns_422(app, db_session, client):
    """ PATCH con payload vacio {}. Verificar 422 VALIDATION_ERROR """
    cat = _make_category(db_session, name="Cat_MissingActive")
    skill = _make_skill(db_session, cat.id, name="Skill_MissingActive")
    user = _make_user(db_session, email="missing_active@example.com")
    alert = _make_alert(db_session, user.id, skill.id)
    alert_id = alert.id
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    response = client.patch(
        f"/api/alerts/{alert_id}/status",
        json={},
        headers={"X-CSRF-TOKEN": csrf}
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_status_not_owned_returns_404(app, db_session, client):
    """ Intento de modificar estado de alerta ajena. Verificar 404 NOT_FOUND y que estado no cambia """
    cat = _make_category(db_session, name="Cat_PatchNotOwned")
    skill = _make_skill(db_session, cat.id, name="Skill_PatchNotOwned")
    user1 = _make_user(db_session, email="patch_not_owned1@example.com")
    user2 = _make_user(db_session, email="patch_not_owned2@example.com")
    
    # Alerta de user2, activa por defecto
    alert2 = _make_alert(db_session, user2.id, skill.id, active=True)
    alert2_id = alert2.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user1.id)

    client.set_cookie("access_token_cookie", token)
    response = client.patch(
        f"/api/alerts/{alert2_id}/status",
        json={"active": False},
        headers={"X-CSRF-TOKEN": csrf}
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"

    db_session.expire_all()
    persisted = db_session.get(Alert, alert2_id)
    assert persisted.active is True


def test_update_status_nonexistent_alert_returns_404(app, db_session, client):
    """ PATCH a ID inexistente retorna 404 """
    user = _make_user(db_session, email="patch_nonexist@example.com")
    user_id = user.id

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    response = client.patch(
        "/api/alerts/999999/status",
        json={"active": False},
        headers={"X-CSRF-TOKEN": csrf}
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def _make_snapshot(db_session, skill_id, demand_count=None, growth_rate=None,
                   snap_date=None, city_id=None):
    from app.models.trend_snapshot import TrendSnapshot
    from datetime import date
    snap = TrendSnapshot(
        skill_id=skill_id,
        city_id=city_id,
        date=snap_date or date(2025, 1, 1),
        demand_count=demand_count,
        growth_rate=growth_rate,
    )
    db_session.add(snap)
    db_session.flush()
    return snap


def test_deactivated_alert_is_excluded_from_evaluation(app, db_session, client, monkeypatch):
    """ Confirmar que PATCH /status conecta con la exclusión de AlertsService.evaluate_and_notify() """
    from unittest.mock import MagicMock
    from app.services.alerts_service import AlertsService
    from datetime import date
    from app.models.trend_snapshot import TrendSnapshot
    
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.alerts_service.send_alert_email", mock_send)

    cat = _make_category(db_session, name="Cat_EndToEnd")
    skill = _make_skill(db_session, cat.id, name="Skill_EndToEnd")
    user = _make_user(db_session, email="end_to_end@example.com")
    
    # Snapshot que cumple sobradamente el threshold (100 >= 50)
    _make_snapshot(db_session, skill.id, demand_count=100, snap_date=date(2025, 1, 2))
    alert = _make_alert(db_session, user.id, skill.id, alert_type="ABSOLUTE", threshold_value=50, active=True)
    alert_id = alert.id
    user_id = user.id

    # Comprobamos que con active=True la alerta SI se dispara
    with app.app_context():
        result_active = AlertsService.evaluate_and_notify()
    
    assert result_active == 1
    mock_send.assert_called_once()
    mock_send.reset_mock()

    # Desactivamos via el endpoint REST
    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    patch_response = client.patch(
        f"/api/alerts/{alert_id}/status",
        json={"active": False},
        headers={"X-CSRF-TOKEN": csrf}
    )
    assert patch_response.status_code == 200

    # Comprobamos que al estar desactivada ya NO se dispara
    with app.app_context():
        result_inactive = AlertsService.evaluate_and_notify()
    
    assert result_inactive == 0
    mock_send.assert_not_called()


def test_create_alert_rejects_when_active_limit_reached(app, db_session, client):
    """ POST a /api/alerts/ cuando el usuario ya tiene 20 alertas activas. Verificar 422 LIMIT_EXCEEDED y que la alerta 21 no se crea """
    from sqlalchemy import select
    
    cat = _make_category(db_session, name="Cat_Limit")
    skill = _make_skill(db_session, cat.id, name="Skill_Limit")
    user = _make_user(db_session, email="limit_reached@example.com")
    skill_id = skill.id
    user_id = user.id

    # Crear 20 alertas activas
    for _ in range(20):
        _make_alert(db_session, user_id, skill_id)

    with app.app_context():
        token, csrf = _mint_token_and_csrf(user_id)

    client.set_cookie("access_token_cookie", token)
    
    # Intentar crear la alerta 21
    payload = {"skill_id": skill_id, "alert_type": "ABSOLUTE", "threshold_value": 100}
    response = client.post("/api/alerts/", json=payload, headers={"X-CSRF-TOKEN": csrf})

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "LIMIT_EXCEEDED"
    assert response.get_json()["error"]["message"] == "Has alcanzado el límite de 20 alertas activas."

    # Verificar que las alertas en BD sigan siendo exactamente 20
    db_session.expire_all()
    user_alerts = db_session.execute(select(Alert).filter_by(user_id=user_id)).scalars().all()
    assert len(user_alerts) == 20