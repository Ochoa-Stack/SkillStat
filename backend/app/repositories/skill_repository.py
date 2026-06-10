from app.repositories.base_repository import BaseRepository
from app.models import Skill


class SkillRepository(BaseRepository):
    def __init__(self):
        super().__init__(Skill)
