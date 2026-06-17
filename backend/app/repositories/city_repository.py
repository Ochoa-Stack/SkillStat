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
