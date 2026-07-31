from app.repositories.city_repository import CityRepository
from app.clients.nominatim_client import NominatimClient
from app.utils.errors import ConflictError

class CityService:
    # Orquesta la resolucion de ciudades, va desde la busqueda local indexada, geocodificacion externa via Nominatim, y persistencia. Antes esta orquestacion vivia dentro de CityRepository, violando la separacion de capas de nuestra arquitectura de trabajo (Architecture Hexagonal).

    @classmethod
    def get_or_create_city(cls, raw_location: str) -> tuple:
        if not raw_location:
            return None, False

        existing = CityRepository.find_by_normalized_name(raw_location)
        if existing:
            return existing, False

        geo_data = NominatimClient.geocode_city(raw_location)
        if not geo_data:
            return None, False

        # Nominatim puede resolver un alias (ej. "Distrito Federal") a un nombre real (ej. "Ciudad de Mexico") que ya exista en BD.
        resolved_name = geo_data["name"]
        existing_resolved = CityRepository.find_by_normalized_name(resolved_name)
        if existing_resolved:
            return existing_resolved, False

        try:
            new_city = CityRepository.create({
                "name": geo_data["name"],
                "state": geo_data["state"],
                "lat": geo_data["lat"],
                "lon": geo_data["lon"],
            })
            return new_city, True
        except ConflictError:
            # Condicion de carrera: otro proceso concurrente ya inserto esta misma ciudad entre nuestra verificacion y nuestro intento de creacion. La constraint unique=True de City.name disparo el conflicto; recuperamos la fila que el otro proceso ya persistio, en vez de fallar la ingesta.
            return CityRepository.find_by_normalized_name(resolved_name), False
