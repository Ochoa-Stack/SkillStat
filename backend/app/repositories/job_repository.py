from app.repositories.base_repository import BaseRepository
from app.models import Job


class JobRepository(BaseRepository):
    def __init__(self):
        super().__init__(Job)
