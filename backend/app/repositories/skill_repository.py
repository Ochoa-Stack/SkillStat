from app.models.skill import Skill
from app.repositories.base_repository import BaseRepository
from app.extensions import db

class SkillRepository(BaseRepository):
    model = Skill

    @classmethod
    def get_by_name(cls, name: str) -> Skill:
        # Buscamos ignorando mayúsculas/minúsculas para evitar duplicados en ingesta
        from sqlalchemy import func
        return db.session.execute(
            db.select(Skill).filter(func.lower(Skill.name) == name.lower())
        ).scalar_one_or_none()

    @classmethod
    def get_by_canonical_name(cls, canonical_name: str) -> Skill:
        return db.session.execute(
            db.select(Skill).filter_by(canonical_name=canonical_name)
        ).scalar_one_or_none()
