from app.repositories.base_repository import BaseRepository
from app.models.city import City
from app.extensions import db

class CityRepository(BaseRepository):
    model = City

    @classmethod
    def get_by_name(cls, name: str):
        return db.session.execute(
            db.select(City).filter_by(name=name)
        ).scalar_one_or_none()

    @classmethod
    def find_by_normalized_name(cls, raw_name: str):
        # Usa unaccent() nativo de PostgreSQL para busqueda insensible a acentos y mayusculas, reemplazando el escaneo completo en memoria que hacia _normalize. Sin indice funcional (unaccent de un solo argumento es STABLE, no IMMUTABLE, y el wrapper IMMUTABLE resulto incompatible entre versiones de PostgreSQL), aceptable dado el volumen actual del catalogo de ciudades; escanea la tabla completa en el motor, no en Python, que ya es la mejora real sobre el comportamiento anterior.
        if not raw_name:
            return None
        raw_name = raw_name.strip()
        from sqlalchemy import func
        normalized_input = func.unaccent(func.lower(raw_name))
        return db.session.execute(
            db.select(City).filter(
                func.unaccent(func.lower(City.name)) == normalized_input
            )
        ).scalar_one_or_none()
