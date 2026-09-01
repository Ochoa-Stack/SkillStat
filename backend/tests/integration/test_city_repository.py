import pytest
from unittest.mock import MagicMock

from app.models.city import City
from app.repositories.city_repository import CityRepository

def _make_city(db_session, name="Ciudad Test", state="Estado Test", lat=19.4326, lon=-99.1332):
    city = City(name=name, state=state, lat=lat, lon=lon, country="MX")
    db_session.add(city)
    db_session.commit()
    return city

def test_get_by_name_returns_city_if_exists(app, db_session):
    """ get_by_name retorna la ciudad correcta cuando existe, y None cuando no. """
    _make_city(db_session, name="Cancún")
    
    with app.app_context():
        city_found = CityRepository.get_by_name("Cancún")
        city_missing = CityRepository.get_by_name("Mérida")
        assert city_found is not None
        assert city_found.name == "Cancún"
        assert city_missing is None
