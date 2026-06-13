from app.models.job import Job
from app.repositories.base_repository import BaseRepository

class JobRepository(BaseRepository):
    model = Job
