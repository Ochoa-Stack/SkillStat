import time
import logging
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class NominatimClient:
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "SkillStat/1.0 (proyecto academico UTCJ, contacto: 195959137+Ochoa-Stack@users.noreply.github.com)"
    
    # Valid types that represent a real city/town/village entity.
    VALID_TYPES = {"city", "town", "village", "municipality"}
    
    # Desambiguación para mapear queries ambiguos (o estados homónimos) a sus ciudades reales.
    QUERY_DISAMBIGUATION = {
        "cdmx": "Ciudad de Mexico",
        "distrito federal": "Ciudad de Mexico",
        "df": "Ciudad de Mexico",
        "mexico df": "Ciudad de Mexico",
        "puebla": "Puebla de Zaragoza",
        "queretaro": "Santiago de Queretaro",
        "oaxaca": "Oaxaca, Oaxaca",
        "guanajuato": "Guanajuato, Guanajuato",
        "campeche": "Campeche, Campeche",
        "colima": "Colima, Colima",
        "chihuahua": "Chihuahua, Chihuahua",
        "durango": "Durango, Durango",
        "tlaxcala": "Tlaxcala, Tlaxcala",
        "zacatecas": "Zacatecas, Zacatecas"
    }

    @classmethod
    def _resolve_query(cls, query: str) -> str:
        import unicodedata
        normalized_query = query.strip().lower()
        normalized_query = ''.join(c for c in unicodedata.normalize('NFD', normalized_query) if unicodedata.category(c) != 'Mn')
        normalized_query = normalized_query.replace(".", "")
        return cls.QUERY_DISAMBIGUATION.get(normalized_query, query)

    @classmethod
    def _is_valid_place_type(cls, result: dict) -> bool:
        place_type = result.get("type", "").lower()
        place_class = result.get("class", "").lower()
        addresstype = result.get("addresstype", "").lower()
        return place_type in cls.VALID_TYPES or place_class in cls.VALID_TYPES or addresstype in cls.VALID_TYPES

    @classmethod
    def _extract_city_name(cls, result: dict) -> str | None:
        address = result.get("address", {})
        return address.get("city") or address.get("town") or address.get("village") or address.get("municipality") or result.get("name")

    @classmethod
    def geocode_city(cls, query: str) -> dict | None:
        """ Geocodes a city name using Nominatim API. Returns a dict with 'name', 'state', 'lat', 'lon' or None if it fails, timeouts, or doesn't meet the confidence threshold (must have state, must be a valid city type) """
        actual_query = cls._resolve_query(query)
        
        # Sleep to respect Nominatim's strict 1 req/sec limit
        time.sleep(1.1)
        
        headers = {
            "User-Agent": cls.USER_AGENT
        }
        params = {
            "q": actual_query,
            "format": "jsonv2",
            "countrycodes": "mx",
            "limit": 1,
            "addressdetails": 1
        }
        
        try:
            response = requests.get(cls.BASE_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return None
                
            result = data[0]
            
            if not cls._is_valid_place_type(result):
                return None
                
            address = result.get("address", {})
            state = address.get("state")
            
            if not state:
                return None
                
            name = cls._extract_city_name(result)
            
            if not name:
                return None
                
            return {
                "name": name,
                "state": state,
                "lat": float(result.get("lat")),
                "lon": float(result.get("lon"))
            }
            
        except RequestException as e:
            logger.warning(f"Error de conexion o timeout al contactar Nominatim para query '{query}': {e}")
            return None
        except ValueError as e:
            logger.warning(f"Error decodificando respuesta JSON de Nominatim para query '{query}': {e}")
            return None
