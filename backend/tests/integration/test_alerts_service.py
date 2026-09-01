import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock

from app.models.user import User
from app.models.skill import Skill
from app.models.category import Category
from app.models.alert import Alert
from app.models.trend_snapshot import TrendSnapshot
from app.services.alerts_service import AlertsService
from app.utils.errors import AppError


""" Helpers de creacion de entidades.
Creamos Category inline en cada test (principio DAMP: cada test es autocontenido). No existe fixture de seed reutilizable en el proyecto para Category, y el modelo solo requiere name unico, por lo que es mas claro y directo crearla inline. Usamos nombres distintos por test para evitar conflictos de unicidad entre tests que corran en la misma transaccion """


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
    db_session.flush()
    return user


def _make_snapshot(db_session, skill_id, demand_count=None, growth_rate=None,
                   snap_date=None, city_id=None):
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


def _make_alert(db_session, user_id, skill_id, alert_type, threshold_value=None,
                threshold_percentage=None, active=True):
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
    return alert


# Tests

def test_inactive_alerts_are_never_evaluated(app, db_session, monkeypatch):
    """ AlertRepository.get_all() sin filtrar active=True evaluaba alertas que el usuario ya habia desactivado, potencialmente enviando notificaciones no deseadas. Verificamos que una alerta inactiva con un threshold que claramente se cumpliria nunca genera ninguna notificacion """
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.alerts_service.send_alert_email", mock_send)

    cat = _make_category(db_session, name="Cat_Inactive")
    skill = _make_skill(db_session, cat.id, name="Skill_Inactive")
    user = _make_user(db_session, email="inactive_alert@example.com")
    _make_snapshot(db_session, skill.id, demand_count=9999, snap_date=date(2025, 1, 1))
    _make_alert(db_session, user.id, skill.id, alert_type="ABSOLUTE",
                threshold_value=1, active=False)

    with app.app_context():
        result = AlertsService.evaluate_and_notify()

    assert result == 0
    mock_send.assert_not_called()


def test_absolute_alert_triggers_when_threshold_met(app, db_session, monkeypatch):
    """ Una alerta ABSOLUTE activa debe dispararse cuando demand_count del snapshot mas reciente supera o iguala threshold_value """
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.alerts_service.send_alert_email", mock_send)

    cat = _make_category(db_session, name="Cat_AbsTrue")
    skill = _make_skill(db_session, cat.id, name="Skill_AbsTrue")
    user = _make_user(db_session, email="abs_trigger@example.com")
    _make_snapshot(db_session, skill.id, demand_count=100, snap_date=date(2025, 1, 2))
    _make_alert(db_session, user.id, skill.id, alert_type="ABSOLUTE", threshold_value=50)

    with app.app_context():
        result = AlertsService.evaluate_and_notify()

    assert result == 1
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0]
    assert call_args[0] == user.email


def test_absolute_alert_does_not_trigger_below_threshold(app, db_session, monkeypatch):
    """ Una alerta ABSOLUTE no debe dispararse cuando demand_count es menor que
    threshold_value """
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.alerts_service.send_alert_email", mock_send)

    cat = _make_category(db_session, name="Cat_AbsFalse")
    skill = _make_skill(db_session, cat.id, name="Skill_AbsFalse")
    user = _make_user(db_session, email="abs_no_trigger@example.com")
    _make_snapshot(db_session, skill.id, demand_count=10, snap_date=date(2025, 1, 3))
    _make_alert(db_session, user.id, skill.id, alert_type="ABSOLUTE", threshold_value=50)

    with app.app_context():
        result = AlertsService.evaluate_and_notify()

    assert result == 0
    mock_send.assert_not_called()


def test_trend_alert_triggers_when_growth_rate_met(app, db_session, monkeypatch):
    """ Una alerta TREND activa debe dispararse cuando growth_rate del snapshot mas reciente supera o iguala threshold_percentage """
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.alerts_service.send_alert_email", mock_send)

    cat = _make_category(db_session, name="Cat_TrendTrue")
    skill = _make_skill(db_session, cat.id, name="Skill_TrendTrue")
    user = _make_user(db_session, email="trend_trigger@example.com")
    _make_snapshot(db_session, skill.id, growth_rate=Decimal("20.0"), snap_date=date(2025, 1, 4))
    _make_alert(db_session, user.id, skill.id, alert_type="TREND",
                threshold_percentage=Decimal("15.0"))

    with app.app_context():
        result = AlertsService.evaluate_and_notify()

    assert result == 1
    mock_send.assert_called_once()


def test_trend_alert_not_evaluated_when_growth_rate_is_null(app, db_session, monkeypatch):
    """ Un growth_rate=None en el snapshot significa que no hay suficiente historial para calcular el crecimiento semanal. La logica de produccion trata este caso como 'no evaluar', no como 'umbral no cumplido'. El test confirma que ningun email se envia en esta situacion """
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.alerts_service.send_alert_email", mock_send)

    cat = _make_category(db_session, name="Cat_TrendNull")
    skill = _make_skill(db_session, cat.id, name="Skill_TrendNull")
    user = _make_user(db_session, email="trend_null@example.com")
    _make_snapshot(db_session, skill.id, growth_rate=None, snap_date=date(2025, 1, 5))
    _make_alert(db_session, user.id, skill.id, alert_type="TREND",
                threshold_percentage=Decimal("15.0"))

    with app.app_context():
        result = AlertsService.evaluate_and_notify()

    assert result == 0
    mock_send.assert_not_called()


def test_alert_skipped_when_no_trend_snapshot_exists(app, db_session, monkeypatch):
    """ Si no existe ningun TrendSnapshot para el skill de la alerta, evaluate_and_notify debe saltar la alerta silenciosamente y retornar 0 sin lanzar ninguna excepcion """
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.alerts_service.send_alert_email", mock_send)

    cat = _make_category(db_session, name="Cat_NoSnap")
    skill = _make_skill(db_session, cat.id, name="Skill_NoSnap")
    user = _make_user(db_session, email="no_snapshot@example.com")
    # No creamos ningun TrendSnapshot para este skill.
    _make_alert(db_session, user.id, skill.id, alert_type="ABSOLUTE", threshold_value=50)

    with app.app_context():
        result = AlertsService.evaluate_and_notify()

    assert result == 0
    mock_send.assert_not_called()


def test_email_failure_does_not_interrupt_processing(app, db_session, monkeypatch):
    """ Si send_alert_email lanza AppError para la primera alerta, el servicio debe capturarla silenciosamente, continuar con la segunda alerta, y retornar 1 (solo la notificacion exitosa cuenta). La excepcion de la primera no interrumpe el ciclo """
    call_count = {"n": 0}

    def send_side_effect(email, subject, html):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise AppError("Fallo simulado de email", status_code=500, code="EMAIL_ERROR")

    monkeypatch.setattr("app.services.alerts_service.send_alert_email", send_side_effect)

    cat = _make_category(db_session, name="Cat_EmailFail")
    skill1 = _make_skill(db_session, cat.id, name="Skill_EmailFail1")
    skill2 = _make_skill(db_session, cat.id, name="Skill_EmailFail2")
    user = _make_user(db_session, email="email_fail@example.com")

    # Ambas alertas tienen snapshots que superan el umbral.
    _make_snapshot(db_session, skill1.id, demand_count=200, snap_date=date(2025, 1, 6))
    _make_snapshot(db_session, skill2.id, demand_count=200, snap_date=date(2025, 1, 7))
    _make_alert(db_session, user.id, skill1.id, alert_type="ABSOLUTE", threshold_value=50)
    _make_alert(db_session, user.id, skill2.id, alert_type="ABSOLUTE", threshold_value=50)

    with app.app_context():
        result = AlertsService.evaluate_and_notify()

    # Solo la segunda notificacion tuvo exito.
    assert result == 1
    assert call_count["n"] == 2
