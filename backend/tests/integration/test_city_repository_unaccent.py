import pytest
from sqlalchemy import event
from app.extensions import db as _db
from app.models.city import City
from app.repositories.city_repository import CityRepository

@pytest.fixture
def query_counter(app):
    counts = {"n": 0}
    def on_execute(conn, cursor, statement, parameters, context, executemany):
        counts["n"] += 1
    event.listen(_db.engine, "before_cursor_execute", on_execute)
    yield counts
    event.remove(_db.engine, "before_cursor_execute", on_execute)

def _make_city(db_session, name="Guadalajara"):
    city = City(name=name, state="State", country="MX")
    db_session.add(city)
    db_session.flush()
    return city

def test_find_by_normalized_name_matches_exact(app, db_session):
    _make_city(db_session, name="Guadalajara")
    
    with app.app_context():
        city = CityRepository.find_by_normalized_name("Guadalajara")
        assert city is not None
        assert city.name == "Guadalajara"

def test_find_by_normalized_name_matches_with_accents_and_case(app, db_session):
    _make_city(db_session, name="Querétaro")
    
    with app.app_context():
        city = CityRepository.find_by_normalized_name("  queretaro  ")
        assert city is not None
        assert city.name == "Querétaro"

def test_find_by_normalized_name_returns_none_when_not_found(app, db_session):
    _make_city(db_session, name="Monterrey")
    
    with app.app_context():
        city = CityRepository.find_by_normalized_name("Cancun")
        assert city is None

def test_find_by_normalized_name_returns_none_for_empty_string(app, db_session):
    with app.app_context():
        city = CityRepository.find_by_normalized_name("")
        assert city is None
        
        city_none = CityRepository.find_by_normalized_name(None)
        assert city_none is None

def test_find_by_normalized_name_uses_single_query(app, db_session, query_counter):
    _make_city(db_session, name="Mérida")
    
    with app.app_context():
        query_counter["n"] = 0
        city = CityRepository.find_by_normalized_name("merida")
        assert city is not None
        assert city.name == "Mérida"
        assert query_counter["n"] == 1
