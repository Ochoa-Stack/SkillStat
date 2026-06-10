from app.repositories.base_repository import BaseRepository
from app.models import User

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)