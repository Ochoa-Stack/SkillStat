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

    @classmethod
    def get_salary_stats(cls, skill_id: int):
        from sqlalchemy import func
        from app.models.job import Job
        from app.models.job_skill import JobSkill

        # Solo consideramos vacantes que efectivamente declaran ambos extremos del rango salarial para no distorsionar el promedio con ceros o valores parciales.
        return db.session.execute(
            db.select(
                func.avg(Job.salary_min).label("avg_salary_min"),
                func.avg(Job.salary_max).label("avg_salary_max"),
                func.count(Job.id).label("sample_size"),
            )
            .join(JobSkill, JobSkill.job_id == Job.id)
            .filter(JobSkill.skill_id == skill_id)
            .filter(Job.salary_min.isnot(None))
            .filter(Job.salary_max.isnot(None))
        ).first()
