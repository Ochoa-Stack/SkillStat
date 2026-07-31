import uuid
import pytest
from sqlalchemy import event
from datetime import datetime, timezone, timedelta

from app.models.city import City
from app.models.category import Category
from app.models.skill import Skill
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.trend_snapshot import TrendSnapshot
from app.extensions import db as _db

@pytest.fixture
def query_counter(app):
    counts = {"n": 0}
    def on_execute(conn, cursor, statement, parameters, context, executemany):
        counts["n"] += 1
    event.listen(_db.engine, "before_cursor_execute", on_execute)
    yield counts
    event.remove(_db.engine, "before_cursor_execute", on_execute)

# Helpers de creacion de entidades.
# Duplicados deliberadamente aqui (principio DAMP): cada archivo de tests es autocontenido. No se importan desde otros archivos de tests.

def _make_city(db_session, city_id=2, name="Ciudad Test", state="Estado Test"):
    """ Crea una City con id explicito. Usamos city_id!=1 por defecto en este archivo para evitar colision con el fallback de generate_snapshots() que usa city_id=1. Los endpoints de panorama no invocan ese fallback, pero es buena practica no depender de ese ID. """
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

def _make_job(db_session, city_id, salary_min=None, salary_max=None):
    job = Job(
        source="test",
        title="Test Job",
        company="Test Co",
        city_id=city_id,
        salary_min=salary_min,
        salary_max=salary_max,
        raw_description="raw",
        description_hash=str(uuid.uuid4()),
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

def _make_snapshot(db_session, skill_id, city_id, demand_count=10,
                   days_ago=0, growth_rate=None, avg_salary=None):
    """ Inserta un TrendSnapshot directamente (sin pasar por generate_snapshots). days_ago=0 => fecha de hoy; days_ago=7 => hace 7 dias. """
    snap_date = datetime.now(timezone.utc).date() - timedelta(days=days_ago)
    snap = TrendSnapshot(
        skill_id=skill_id,
        city_id=city_id,
        date=snap_date,
        demand_count=demand_count,
        growth_rate=growth_rate,
        avg_salary=avg_salary,
    )
    db_session.add(snap)
    db_session.commit()
    return snap

def _setup_compare_skills(db_session, num_skills=2, base_id=40):
    city = _make_city(db_session, city_id=base_id, name=f"City_Compare_{base_id}")
    cat = _make_category(db_session, name=f"Cat_Compare_{base_id}")
    skill_ids = []
    for i in range(num_skills):
        skill = _make_skill(db_session, cat.id, name=f"Skill_Compare_{base_id}_{i}")
        _make_snapshot(db_session, skill.id, city.id, demand_count=(i+1)*5)
        skill_ids.append(skill.id)
    return skill_ids

# GET /api/panorama/skills

def test_get_skills_returns_all(app, db_session, client):
    """ Crear dos skills reales. Verificar que ambas aparecen en la respuesta con 200. Se verifica por id, no por conteo exacto, porque otros tests dentro de la misma sesion pueden haber insertado skills adicionales."""
    cat = _make_category(db_session, name="Cat_Skills")
    skill_a = _make_skill(db_session, cat.id, name="SkillA_GetAll")
    skill_b = _make_skill(db_session, cat.id, name="SkillB_GetAll")
    skill_a_id = skill_a.id
    skill_b_id = skill_b.id

    response = client.get("/api/panorama/skills")

    assert response.status_code == 200
    returned_ids = {s["id"] for s in response.get_json()["data"]}
    assert skill_a_id in returned_ids
    assert skill_b_id in returned_ids


# GET /api/panorama/catalogs

def test_get_catalogs_returns_skills_and_cities(app, db_session, client):
    """ Crear una city y un skill reales. Verificar 200 y que la respuesta contiene ambas listas con los campos id+name esperados. """
    city = _make_city(db_session, city_id=10, name="City_Catalogs")
    cat = _make_category(db_session, name="Cat_Catalogs")
    skill = _make_skill(db_session, cat.id, name="Skill_Catalogs")
    city_id = city.id
    skill_id = skill.id

    response = client.get("/api/panorama/catalogs")

    assert response.status_code == 200
    data = response.get_json()["data"]

    assert "skills" in data
    assert "cities" in data

    returned_skill_ids = {s["id"] for s in data["skills"]}
    returned_city_ids = {c["id"] for c in data["cities"]}

    assert skill_id in returned_skill_ids
    assert city_id in returned_city_ids

    any_skill = next(s for s in data["skills"] if s["id"] == skill_id)
    assert "name" in any_skill
    any_city = next(c for c in data["cities"] if c["id"] == city_id)
    assert "name" in any_city

# GET /api/panorama/summary

def test_get_summary_returns_kpis(app, db_session, client):
    """ Crear datos minimos (job, skill, snapshot) y verificar que summary retorna 200 con los campos KPI estructurales esperados. No se verifican valores exactos de agregacion porque otros tests de la sesion pueden haber insertado datos adicionales — verificamos estructura y >= minimos. """
    city = _make_city(db_session, city_id=20, name="City_Summary")
    cat = _make_category(db_session, name="Cat_Summary")
    skill = _make_skill(db_session, cat.id, name="Skill_Summary")
    _make_job(db_session, city_id=city.id)
    _make_snapshot(db_session, skill.id, city.id, demand_count=5)

    response = client.get("/api/panorama/summary")

    assert response.status_code == 200
    data = response.get_json()["data"]

    assert "total_jobs" in data
    assert "total_skills_tracked" in data
    assert "total_companies" in data
    assert data["total_jobs"] >= 1
    assert data["total_skills_tracked"] >= 1

# GET /api/panorama/skills/top

def test_get_skills_top_respects_limit_bounds(app, client):
    """ Verificar que limit se acota segun max(1, min(limit, 50)) del codigo. No se necesitan 50 snapshots reales; verificamos que el endpoint responde 200 para ambos extremos y devuelve una lista valida. """
    # limit=0 => max(1, min(0, 50)) = 1 - no debe fallar
    resp_zero = client.get("/api/panorama/skills/top?limit=0")
    assert resp_zero.status_code == 200
    assert isinstance(resp_zero.get_json()["data"], list)

    # limit=1000 => max(1, min(1000, 50)) = 50 — no debe fallar
    resp_over = client.get("/api/panorama/skills/top?limit=1000")
    assert resp_over.status_code == 200
    assert isinstance(resp_over.get_json()["data"], list)

# GET /api/panorama/trends

def test_get_trends_requires_skill_id(app, client):
    """ GET sin parametro skill_id debe retornar 422 VALIDATION_ERROR. """
    response = client.get("/api/panorama/trends")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

def test_get_trends_returns_404_for_nonexistent_skill(app, client):
    """ GET con skill_id inexistente debe retornar 404 NOT_FOUND. """
    response = client.get("/api/panorama/trends?skill_id=999999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"

def test_get_trends_returns_series_for_valid_skill(app, db_session, client):
    """ Crear skill con un trend_snapshot. Verificar 200 y que la serie temporal incluye la fecha del snapshot insertado. """
    city = _make_city(db_session, city_id=30, name="City_Trends")
    cat = _make_category(db_session, name="Cat_Trends")
    skill = _make_skill(db_session, cat.id, name="Skill_Trends")
    snap = _make_snapshot(db_session, skill.id, city.id, demand_count=7)
    skill_id = skill.id
    snap_date = snap.date

    response = client.get(f"/api/panorama/trends?skill_id={skill_id}")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["skill_id"] == skill_id
    assert "series" in data

    series_dates = [s["date"] for s in data["series"]]
    assert str(snap_date) in series_dates

# GET /api/panorama/geo

def test_get_geo_rejects_invalid_group_by(app, client):
    """ group_by distinto de 'city' o 'state' debe retornar 422. """
    response = client.get("/api/panorama/geo?group_by=invalid")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

def test_get_geo_returns_404_for_nonexistent_skill(app, client):
    """ skill_id inexistente debe retornar 404 NOT_FOUND. """
    response = client.get("/api/panorama/geo?skill_id=999999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"

def test_get_geo_returns_200_without_skill_filter(app, client):
    """ Sin skill_id el endpoint debe retornar 200 con distribucion global (puede estar vacia si no hay snapshots, pero no debe fallar). """
    response = client.get("/api/panorama/geo")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert "distribution" in data
    assert isinstance(data["distribution"], list)

# GET /api/panorama/salaries

def test_get_salaries_requires_skill_id(app, client):
    """ GET sin skill_id debe retornar 422 VALIDATION_ERROR. """
    response = client.get("/api/panorama/salaries")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

def test_get_salaries_returns_404_for_nonexistent_skill(app, client):
    """ skill_id inexistente debe retornar 404 NOT_FOUND. """
    response = client.get("/api/panorama/salaries?skill_id=999999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"

# GET /api/panorama/compare

def test_get_compare_requires_between_2_and_5_skills(app, db_session, client):
    """ Probar con 1 skill (menos de 2) y con 6 skills (mas de 5). Ambos deben retornar 422 VALIDATION_ERROR. """
    cat = _make_category(db_session, name="Cat_Compare_Bounds")
    skills = [_make_skill(db_session, cat.id, name=f"Skill_Bound_{i}") for i in range(6)]
    ids = [s.id for s in skills]

    # Un solo skill — menor al minimo de 2
    resp_one = client.get(f"/api/panorama/compare?skill_ids={ids[0]}")
    assert resp_one.status_code == 422
    assert resp_one.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # Seis skills — excede el maximo de 5
    ids_str = ",".join(str(i) for i in ids)
    resp_six = client.get(f"/api/panorama/compare?skill_ids={ids_str}")
    assert resp_six.status_code == 422
    assert resp_six.get_json()["error"]["code"] == "VALIDATION_ERROR"

def test_get_compare_returns_404_when_any_skill_missing(app, db_session, client):
    """ Un skill real + un id inexistente debe retornar 404 NOT_FOUND. """
    cat = _make_category(db_session, name="Cat_Compare_404")
    skill = _make_skill(db_session, cat.id, name="Skill_Compare_404")
    skill_id = skill.id

    response = client.get(f"/api/panorama/compare?skill_ids={skill_id},999999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"

def test_get_compare_success_with_valid_skills(app, db_session, client):
    """ Crear dos skills con al menos un snapshot cada uno. Verificar 200 y que la respuesta incluye un bloque por cada skill solicitado. """
    skill_ids = _setup_compare_skills(db_session, num_skills=2, base_id=40)
    id_a, id_b = skill_ids

    response = client.get(f"/api/panorama/compare?skill_ids={id_a},{id_b}")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert "skills" in data

    returned_skill_ids = {block["skill_id"] for block in data["skills"]}
    assert id_a in returned_skill_ids
    assert id_b in returned_skill_ids

def test_get_compare_query_count_baseline_before_optimization(
    client, db_session, query_counter
):
    """ Test de caracterización: documenta el número EXACTO de queries que get_compare ejecuta hoy con 5 skills (patrón N+1 confirmado en auditoría: hasta 15 queries). Este test debe actualizarse, no eliminarse, cuando la Ronda 3 introduzca los métodos batch. """
    skill_ids = _setup_compare_skills(db_session, num_skills=5, base_id=50)
    ids_str = ",".join(str(i) for i in skill_ids)

    query_counter["n"] = 0
    response = client.get(f"/api/panorama/compare?skill_ids={ids_str}")

    assert response.status_code == 200
    
    assert query_counter["n"] == 15
