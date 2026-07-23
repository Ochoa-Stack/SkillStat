import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.models.user import User
from app.models.city import City
from app.models.category import Category
from app.models.skill import Skill
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.trend_snapshot import TrendSnapshot
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.services.market_trends_service import MarketTrendsService
from app.extensions import db as _db


# Helpers de creacion de entidades.
# Duplicados deliberadamente aqui (principio DAMP): cada archivo de tests es autocontenido. No se importa desde otros archivos de tests para preservar aislamiento y legibilidad individual.

def _make_city(db_session, city_id, name="Mexico Nacional", state="Nacional"):
    """ Crea una City con un ID especifico usando INSERT directo para poder controlar el id=1 que necesita el fallback de generate_snapshots(). Usa INSERT con id explicito en lugar de add() para garantizar el id exacto, ya que PostgreSQL asigna secuencias y podria saltarse el 1 si ya hubo inserts previos en la sesion """
    city = City(id=city_id, name=name, state=state)
    db_session.add(city)
    db_session.flush()
    return city


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


def _make_job(db_session, city_id, description_hash=None, salary_min=None, salary_max=None):
    """ Crea un Job con created_at reciente (ahora mismo en UTC) para que JobSkillRepository.get_active(days=30) lo incluya siempre """
    import uuid
    hash_val = description_hash or str(uuid.uuid4())
    job = Job(
        source="test",
        title="Test Job",
        company="Test Co",
        city_id=city_id,
        salary_min=salary_min,
        salary_max=salary_max,
        raw_description="raw",
        description_hash=hash_val,
        processed=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(job)
    db_session.flush()
    return job


def _make_job_skill(db_session, job_id, skill_id, confidence_score=0.9):
    js = JobSkill(
        job_id=job_id,
        skill_id=skill_id,
        confidence_score=confidence_score,
    )
    db_session.add(js)
    db_session.flush()
    return js


def _make_prev_snapshot(db_session, skill_id, city_id, demand_count, days_ago=7):
    """ Inserta un TrendSnapshot en la fecha exacta que usa generate_snapshots() como referencia de crecimiento: hoy - 7 dias """
    target_date = datetime.now(timezone.utc).date() - timedelta(days=days_ago)
    snap = TrendSnapshot(
        skill_id=skill_id,
        city_id=city_id,
        date=target_date,
        demand_count=demand_count,
        growth_rate=None,
        avg_salary=None,
    )
    db_session.add(snap)
    db_session.commit()
    return snap


def _get_today_snapshot(db_session, skill_id, city_id):
    """ Recupera el snapshot generado para hoy para la combinacion skill+city """
    today = datetime.now(timezone.utc).date()
    return db_session.execute(
        _db.select(TrendSnapshot).filter_by(
            skill_id=skill_id, city_id=city_id, date=today
        )
    ).scalar_one_or_none()


# Tests: MarketTrendsService.generate_snapshots() - escenarios de growth_rate

def test_growth_rate_none_when_no_previous_snapshot(app, db_session):
    """ Si no existe TrendSnapshot previo en (hoy - 7 dias) para la combinacion skill_id+city_id, growth_rate debe ser None. No hay division, no hay base de comparacion """
    city = _make_city(db_session, city_id=1)
    cat = _make_category(db_session, name="Cat_NoPrev")
    skill = _make_skill(db_session, cat.id, name="Skill_NoPrev")
    skill_id = skill.id
    city_id = city.id

    # Creamos un Job+JobSkill reciente - sin snapshot previo en hoy-7dias
    job = _make_job(db_session, city_id=city_id)
    _make_job_skill(db_session, job.id, skill_id)

    # Sin snapshot previo en hoy-7dias para esta combinacion - confirmamos
    target_date = datetime.now(timezone.utc).date() - timedelta(days=7)
    prev = db_session.execute(
        _db.select(TrendSnapshot).filter_by(
            skill_id=skill_id, city_id=city_id, date=target_date
        )
    ).scalar_one_or_none()
    assert prev is None, "Prerequisito: no debe existir snapshot previo para este test"

    with app.app_context():
        MarketTrendsService.generate_snapshots()

    snapshot = _get_today_snapshot(db_session, skill_id, city_id)
    assert snapshot is not None, "generate_snapshots() debe haber creado el snapshot de hoy"
    assert snapshot.growth_rate is None, (
        f"Sin snapshot previo, growth_rate debe ser None, pero fue {snapshot.growth_rate}"
    )


def test_growth_rate_none_when_previous_demand_count_is_zero(app, db_session):
    """ Si el snapshot previo existe pero su demand_count es 0, growth_rate debe ser None para evitar division por cero. La condicion en el codigo es: 'if not prev_snapshot or not prev_snapshot.demand_count' """
    city = _make_city(db_session, city_id=1)
    cat = _make_category(db_session, name="Cat_ZeroPrev")
    skill = _make_skill(db_session, cat.id, name="Skill_ZeroPrev")
    skill_id = skill.id
    city_id = city.id

    # Snapshot previo con demand_count=0 — activa la guarda de division por cero
    _make_prev_snapshot(db_session, skill_id, city_id, demand_count=0)

    job = _make_job(db_session, city_id=city_id)
    _make_job_skill(db_session, job.id, skill_id)

    with app.app_context():
        MarketTrendsService.generate_snapshots()

    snapshot = _get_today_snapshot(db_session, skill_id, city_id)
    assert snapshot is not None
    assert snapshot.growth_rate is None, (
        f"Con demand_count previo=0, growth_rate debe ser None, pero fue {snapshot.growth_rate}"
    )


def test_growth_rate_calculated_within_normal_range(app, db_session):
    """ Calculo normal de growth_rate dentro del rango sin cap. Setup: previo demand_count=10, hoy demand_count=15. Formula: ((15 - 10) / 10) * 100 = 50.0 Valor exacto esperado: Decimal('50.00') (almacenado como Numeric(6,2)) """
    city = _make_city(db_session, city_id=1)
    cat = _make_category(db_session, name="Cat_Normal")
    skill = _make_skill(db_session, cat.id, name="Skill_Normal")
    skill_id = skill.id
    city_id = city.id

    # Snapshot previo con demand_count=10
    _make_prev_snapshot(db_session, skill_id, city_id, demand_count=10)

    # 15 Jobs+JobSkills recientes - demand_count de hoy sera 15
    for i in range(15):
        job = _make_job(db_session, city_id=city_id)
        _make_job_skill(db_session, job.id, skill_id)

    with app.app_context():
        MarketTrendsService.generate_snapshots()

    snapshot = _get_today_snapshot(db_session, skill_id, city_id)
    assert snapshot is not None
    assert snapshot.demand_count == 15

    # Valor exacto: round(((15 - 10) / 10) * 100, 2) = 50.0 => Numeric(6,2) => Decimal('50.00')
    expected = Decimal("50.00")
    assert snapshot.growth_rate == expected, (
        f"growth_rate esperado {expected}, obtenido {snapshot.growth_rate}"
    )


def test_growth_rate_capped_at_positive_999_99(app, db_session):
    """ El cap positivo se aplica cuando el crecimiento calculado excede 999.99. Setup: previo demand_count=1, hoy demand_count=50. Formula sin cap: ((50 - 1) / 1) * 100 = 4900.0 → excede 999.99. Resultado esperado tras cap: Decimal('999.99'). """
    city = _make_city(db_session, city_id=1)
    cat = _make_category(db_session, name="Cat_CapPos")
    skill = _make_skill(db_session, cat.id, name="Skill_CapPos")
    skill_id = skill.id
    city_id = city.id

    # Snapshot previo con demand_count=1 (base minima para crecimiento explosivo)
    _make_prev_snapshot(db_session, skill_id, city_id, demand_count=1)

    # 50 Jobs recientes - da growth_rate=(49/1)*100=4900 antes del cap
    for i in range(50):
        job = _make_job(db_session, city_id=city_id)
        _make_job_skill(db_session, job.id, skill_id)

    with app.app_context():
        MarketTrendsService.generate_snapshots()

    snapshot = _get_today_snapshot(db_session, skill_id, city_id)
    assert snapshot is not None
    assert snapshot.demand_count == 50

    # Sin cap: 4900.0, con cap: 999.99
    expected = Decimal("999.99")
    assert snapshot.growth_rate == expected, (
        f"Cap positivo esperado {expected}, obtenido {snapshot.growth_rate}"
    )


def test_growth_rate_negative_extreme_real_case(app, db_session):
    """ El cap negativo de -999.99 es MATEMATICAMENTE INALCANZABLE con datos reales: demand_count es siempre >= 0 (es un conteo de vacantes), y el peor caso posible es nuevo=0 Jobs activos, pero si no hay Jobs activos, generate_snapshots() retorna 0 sin crear ningun snapshot (la guarda 'if not raw_data: return 0'). Por lo tanto, el demand_count mas bajo fisicamente posible en un snapshot generado es 1, lo que da como caida maxima ((1 - previo) / previo) * 100. Con previo=100 y nuevo=1:
    ((1 - 100) / 100) * 100 = -99.0%, muy lejos del -999.99% del cap.

    Este test verifica el caso mas extremo REAL: previo=100, nuevo=1, -99.00%. El cap negativo queda sin cobertura real posible y se documenta aqui explicitamente como decision de diseno auditada, no como omision. """
    city = _make_city(db_session, city_id=1)
    cat = _make_category(db_session, name="Cat_CapNeg")
    skill = _make_skill(db_session, cat.id, name="Skill_CapNeg")
    skill_id = skill.id
    city_id = city.id

    # Snapshot previo con demand_count=100 (base alta para caida dramatica)
    _make_prev_snapshot(db_session, skill_id, city_id, demand_count=100)

    # Solo 1 Job activo - da la caida mas pronunciada fisicamente posible
    job = _make_job(db_session, city_id=city_id)
    _make_job_skill(db_session, job.id, skill_id)

    with app.app_context():
        MarketTrendsService.generate_snapshots()

    snapshot = _get_today_snapshot(db_session, skill_id, city_id)
    assert snapshot is not None
    assert snapshot.demand_count == 1

    # Formula exacta: round(((1 - 100) / 100) * 100, 2) = -99.0
    # Numeric(6,2) almacena como Decimal('-99.00')
    expected = Decimal("-99.00")
    assert snapshot.growth_rate == expected, (
        f"Caida extrema real esperada {expected}, obtenida {snapshot.growth_rate}"
    )
