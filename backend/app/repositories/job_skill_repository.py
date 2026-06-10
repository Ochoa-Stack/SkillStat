from app.repositories.base_repository import BaseRepository
from app.models import JobSkill

class JobSkillRepository(BaseRepository):
    def __init__(self):
        super().__init__(JobSkill)
