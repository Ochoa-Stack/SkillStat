import pytest
from unittest.mock import MagicMock
from requests.exceptions import RequestException

from app.clients.nominatim_client import NominatimClient

@pytest.fixture
def mock_sleep(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("app.clients.nominatim_client.time.sleep", mock)
    return mock

def test_geocode_city_returns_valid_data(monkeypatch, mock_sleep):
    """ geocode_city retorna un dict con name/state/lat/lon cuando la respuesta de Nominatim es válida y tiene un tipo de lugar en VALID_TYPES. """
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "type": "city",
        "lat": "19.4326",
        "lon": "-99.1332",
        "name": "Ciudad de México",
        "address": {
            "city": "Ciudad de México",
            "state": "Ciudad de México"
        }
    }]
    mock_get = MagicMock(return_value=mock_response)
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", mock_get)

    result = NominatimClient.geocode_city("Ciudad de México")
    
    assert result == {
        "name": "Ciudad de México",
        "state": "Ciudad de México",
        "lat": 19.4326,
        "lon": -99.1332
    }
    mock_sleep.assert_called_once_with(1.1)

def test_geocode_city_returns_none_when_empty_response(monkeypatch, mock_sleep):
    """ geocode_city retorna None cuando la respuesta de Nominatim viene vacía (lista vacía). """
    mock_response = MagicMock()
    mock_response.json.return_value = []
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", MagicMock(return_value=mock_response))

    result = NominatimClient.geocode_city("Ciudad Fantasma")
    assert result is None

def test_geocode_city_returns_none_when_missing_state(monkeypatch, mock_sleep):
    """ geocode_city retorna None cuando el resultado no tiene un state en address (caso de dato insuficiente). """
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "type": "city",
        "lat": "19.4326",
        "lon": "-99.1332",
        "name": "Ciudad de México",
        "address": {
            "city": "Ciudad de México"
            # No state
        }
    }]
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", MagicMock(return_value=mock_response))

    result = NominatimClient.geocode_city("Ciudad sin estado")
    assert result is None

def test_geocode_city_returns_none_when_invalid_type(monkeypatch, mock_sleep):
    """ geocode_city retorna None cuando el tipo de lugar (type/class/addresstype) no está en VALID_TYPES. """
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "type": "residential", # Invalid type
        "lat": "19.4326",
        "lon": "-99.1332",
        "name": "Colonia X",
        "address": {
            "city": "Ciudad",
            "state": "Estado"
        }
    }]
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", MagicMock(return_value=mock_response))

    result = NominatimClient.geocode_city("Colonia")
    assert result is None

def test_geocode_city_applies_disambiguation(monkeypatch, mock_sleep):
    """ geocode_city aplica la desambiguación del diccionario QUERY_DISAMBIGUATION correctamente. """
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "type": "city",
        "lat": "19.4326",
        "lon": "-99.1332",
        "name": "Ciudad de México",
        "address": {
            "city": "Ciudad de México",
            "state": "Ciudad de México"
        }
    }]
    mock_get = MagicMock(return_value=mock_response)
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", mock_get)

    result = NominatimClient.geocode_city("cdmx")
    
    assert result is not None
    called_params = mock_get.call_args[1]["params"]
    assert called_params["q"] == "Ciudad de Mexico"

def test_geocode_city_normalizes_and_applies_disambiguation(monkeypatch, mock_sleep):
    """ geocode_city normaliza el query eliminando acentos y puntos antes de buscar en el diccionario de desambiguación. """
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "type": "city",
        "lat": "19.4326",
        "lon": "-99.1332",
        "name": "Ciudad de México",
        "address": {
            "city": "Ciudad de México",
            "state": "Ciudad de México"
        }
    }]
    mock_get = MagicMock(return_value=mock_response)
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", mock_get)

    result = NominatimClient.geocode_city("  méxico d.f.  ")
    
    assert result is not None
    called_params = mock_get.call_args[1]["params"]
    assert called_params["q"] == "Ciudad de Mexico"

def test_geocode_city_returns_none_on_request_exception(monkeypatch, mock_sleep):
    """ geocode_city retorna None cuando requests.get lanza una excepción de tipo RequestException. """
    mock_get = MagicMock(side_effect=RequestException("Timeout!"))
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", mock_get)

    result = NominatimClient.geocode_city("Cualquier cosa")
    assert result is None

def test_geocode_city_returns_none_on_value_error(monkeypatch, mock_sleep):
    """ geocode_city retorna None cuando la respuesta no es JSON válido (ValueError al parsear). """
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", MagicMock(return_value=mock_response))

    result = NominatimClient.geocode_city("Cualquier cosa")
    assert result is None

def test_geocode_city_uses_name_fallback_priority(monkeypatch, mock_sleep):
    """ Verifica que geocode_city usa como name el primer campo disponible en el orden: city -> town -> village -> municipality -> name """
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "type": "city",
        "lat": "19.4326",
        "lon": "-99.1332",
        "name": "Result Name",
        "address": {
            "state": "Estado",
            "municipality": "Muni",
            "village": "Aldea",
            "town": "Pueblo",
            "city": "Ciudad Principal"
        }
    }]
    monkeypatch.setattr("app.clients.nominatim_client.requests.get", MagicMock(return_value=mock_response))

    result = NominatimClient.geocode_city("Test Priority")
    assert result["name"] == "Ciudad Principal"

    # Caso sin city, debe usar town
    mock_response.json.return_value[0]["address"].pop("city")
    result = NominatimClient.geocode_city("Test Priority")
    assert result["name"] == "Pueblo"

    # Caso sin town, debe usar village
    mock_response.json.return_value[0]["address"].pop("town")
    result = NominatimClient.geocode_city("Test Priority")
    assert result["name"] == "Aldea"

    # Caso sin village, debe usar municipality
    mock_response.json.return_value[0]["address"].pop("village")
    result = NominatimClient.geocode_city("Test Priority")
    assert result["name"] == "Muni"
    
    # Caso sin municipality, debe usar name de result
    mock_response.json.return_value[0]["address"].pop("municipality")
    result = NominatimClient.geocode_city("Test Priority")
    assert result["name"] == "Result Name"
