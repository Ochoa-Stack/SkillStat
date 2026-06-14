from app.models.job import Job
from app.repositories.base_repository import BaseRepository

# La sanitización es manejada dinámicamente por BaseRepository.create
class JobRepository(BaseRepository):
    model = Job
