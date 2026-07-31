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
        # Usa el indice funcional immutable_unaccent(lower(name)) para busqueda insensible a acentos y mayusculas en una sola query indexada, reemplazando el escaneo completo en memoria que hacia _normalize.
        if not raw_name:
            return None
        raw_name = raw_name.strip()
        from sqlalchemy import func
        normalized_input = func.immutable_unaccent(func.lower(raw_name))
        return db.session.execute(
            db.select(City).filter(
                func.immutable_unaccent(func.lower(City.name)) == normalized_input
            )
        ).scalar_one_or_none()
