from app.models.job_skill import JobSkill
from app.repositories.base_repository import BaseRepository

class JobSkillRepository(BaseRepository):
    model = JobSkill
