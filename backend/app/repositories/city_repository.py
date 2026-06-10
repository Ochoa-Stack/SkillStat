from app.repositories.base_repository import BaseRepository
from app.models import City

class CityRepository(BaseRepository):
    def __init__(self):
        super().__init__(City)