import requests
from app.utils.errors import AppError

class NominatimClient:
    # Aislamos el servicio de geocodificación. Nominatim exige un User-Agent válido por sus políticas de uso libre, de lo contrario bloquea la petición.
    BASE_URL = "https://nominatim.openstreetmap.org/search"

    @classmethod
    def geocode(cls, city_name: str, country: str = "Mexico") -> dict:
        params = {
            "city": city_name,
            "country": country,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "SkillStat/1.0 (Student Project UTCJ)"
        }

        try:
            response = requests.get(cls.BASE_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return None
                
            # Devolvemos solo latitud y longitud para mantener el contrato de datos simple
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"])
            }
        except requests.RequestException as e:
            raise AppError(f"Error de geocodificación en Nominatim: {str(e)}", code="EXTERNAL_API_ERROR")
