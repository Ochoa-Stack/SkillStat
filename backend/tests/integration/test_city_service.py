import pytest
from unittest.mock import MagicMock

from app.models.city import City
from app.services.city_service import CityService
from app.repositories.city_repository import CityRepository
from app.utils.errors import ConflictError

def _make_city(db_session, name="Ciudad Test", state="Estado Test", lat=19.4326, lon=-99.1332):
    city = City(name=name, state=state, lat=lat, lon=lon, country="MX")
    db_session.add(city)
    db_session.commit()
    return city

def test_get_or_create_city_returns_existing_exact_match(app, db_session):
    """ get_or_create_city retorna una ciudad existente sin crear una nueva cuando el nombre coincide exactamente. """
    _make_city(db_session, name="Guadalajara")
    
    with app.app_context():
        city, created = CityService.get_or_create_city("Guadalajara")
        assert not created
        assert city is not None
        assert city.name == "Guadalajara"

def test_get_or_create_city_returns_existing_after_normalization(app, db_session):
    """ get_or_create_city retorna una ciudad existente cuando el nombre coincide tras normalización (acentos, mayúsculas/minúsculas). """
    _make_city(db_session, name="Querétaro")
    
    with app.app_context():
        city, created = CityService.get_or_create_city("   queretaro  ")
        assert not created
        assert city is not None
        assert city.name == "Querétaro"

def test_get_or_create_city_creates_new_when_valid_data(app, db_session, monkeypatch):
    """ get_or_create_city crea una ciudad nueva cuando no existe y Nominatim (mockeado) retorna datos válidos, devolviendo (city, True). """
    mock_geocode = MagicMock(return_value={
        "name": "Monterrey",
        "state": "Nuevo León",
        "lat": 25.6866,
        "lon": -100.3161
    })
    monkeypatch.setattr("app.services.city_service.NominatimClient.geocode_city", mock_geocode)
    
    with app.app_context():
        city, created = CityService.get_or_create_city("Monterrey")
        assert created
        assert city is not None
        assert city.name == "Monterrey"
        assert city.state == "Nuevo León"
    mock_geocode.assert_called_once_with("Monterrey")

def test_get_or_create_city_returns_none_when_not_found(app, db_session, monkeypatch):
    """ get_or_create_city retorna (None, False) cuando Nominatim (mockeado) no encuentra resultado. """
    mock_geocode = MagicMock(return_value=None)
    monkeypatch.setattr("app.services.city_service.NominatimClient.geocode_city", mock_geocode)
    
    with app.app_context():
        city, created = CityService.get_or_create_city("Ciudad Inexistente 123")
        assert not created
        assert city is None
    mock_geocode.assert_called_once_with("Ciudad Inexistente 123")

def test_get_or_create_city_detects_resolved_name_already_exists(app, db_session, monkeypatch):
    """ get_or_create_city detecta que el nombre resuelto por Nominatim ya existe en base de datos aunque el nombre original consultado no coincidiera (caso de alias, ej. "Distrito Federal" resolviendo a "Ciudad de México" ya existente) y retorna esa ciudad sin duplicar. """
    _make_city(db_session, name="Ciudad de México")
    
    mock_geocode = MagicMock(return_value={
        "name": "Ciudad de México",
        "state": "Ciudad de México",
        "lat": 19.4326,
        "lon": -99.1332
    })
    monkeypatch.setattr("app.services.city_service.NominatimClient.geocode_city", mock_geocode)
    
    with app.app_context():
        city, created = CityService.get_or_create_city("Distrito Federal")
        assert not created
        assert city is not None
        assert city.name == "Ciudad de México"
    mock_geocode.assert_called_once_with("Distrito Federal")

def test_get_or_create_city_returns_none_for_empty_raw_location(app, db_session):
    """ get_or_create_city retorna (None, False) cuando raw_location está vacío o es None. """
    with app.app_context():
        city1, created1 = CityService.get_or_create_city("")
        city2, created2 = CityService.get_or_create_city(None)
        assert city1 is None
        assert not created1
        assert city2 is None
        assert not created2

def test_get_or_create_city_recovers_from_concurrent_creation_conflict(app, db_session, monkeypatch):
    """ get_or_create_city recupera la ciudad vía find_by_normalized_name si ocurre un ConflictError al intentar insertarla por una colisión en concurrencia con otro proceso. """
    mock_geocode = MagicMock(return_value={
        "name": "Puebla",
        "state": "Puebla",
        "lat": 19.0414,
        "lon": -98.2063
    })
    monkeypatch.setattr("app.services.city_service.NominatimClient.geocode_city", mock_geocode)

    def mock_create(*args, **kwargs):
        # Cuando intenta crearla, simulamos que otro proceso ya la guardo e insertamos directo a BD,
        # y luego lanzamos ConflictError para simular el fallo de integridad del proceso actual.
        _make_city(db_session, name="Puebla", state="Puebla")
        raise ConflictError("Conflicto concurrencia test")

    monkeypatch.setattr("app.services.city_service.CityRepository.create", mock_create)

    with app.app_context():
        city, created = CityService.get_or_create_city("Puebla")
        assert not created
        assert city is not None
        assert city.name == "Puebla"
    mock_geocode.assert_called_once_with("Puebla")
