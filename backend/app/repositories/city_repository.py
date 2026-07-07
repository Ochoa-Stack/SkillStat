from app.repositories.base_repository import BaseRepository
from app.models.city import City
from app.extensions import db
from app.clients.nominatim_client import NominatimClient
import unicodedata

class CityRepository(BaseRepository):
    model = City

    @classmethod
    def get_by_name(cls, name: str):
        return db.session.execute(
            db.select(City).filter_by(name=name)
        ).scalar_one_or_none()
        
    @classmethod
    def get_or_create_city(cls, raw_location: str) -> tuple[City | None, bool]:
        if not raw_location:
            return None, False
            
        # lowercase, sin acentos y trim (Normaliza)
        normalized = raw_location.strip().lower()
        normalized = ''.join(c for c in unicodedata.normalize('NFD', normalized) if unicodedata.category(c) != 'Mn')
        
        # Búsqueda exhaustiva comparando el nombre normalizado
        all_cities = db.session.execute(db.select(City)).scalars().all()
        for city in all_cities:
            city_norm = city.name.strip().lower()
            city_norm = ''.join(c for c in unicodedata.normalize('NFD', city_norm) if unicodedata.category(c) != 'Mn')
            if city_norm == normalized:
                return city, False
                
        # Si no existe, llama a geocode_city
        geo_data = NominatimClient.geocode_city(raw_location)
        if not geo_data:
            return None, False
            
        # Nominatim puede resolver un alias (ej: "Distrito Federal") a un nombre real (ej: "Ciudad de México"). Revisamos si ese nombre real ya existe en BD para evitar IntegrityError secuencial
        resolved_name = geo_data["name"]
        resolved_norm = resolved_name.strip().lower()
        resolved_norm = ''.join(c for c in unicodedata.normalize('NFD', resolved_norm) if unicodedata.category(c) != 'Mn')
        
        for city in all_cities:
            city_norm = city.name.strip().lower()
            city_norm = ''.join(c for c in unicodedata.normalize('NFD', city_norm) if unicodedata.category(c) != 'Mn')
            if city_norm == resolved_norm:
                return city, False
            
        # Si retorna datos válidos y no existe, inserta una nueva fila
        new_city = City(
            name=geo_data["name"],
            state=geo_data["state"],
            lat=geo_data["lat"],
            lon=geo_data["lon"],
            country="MX"
        )
        
        db.session.add(new_city)
        db.session.commit()
        return new_city, True
