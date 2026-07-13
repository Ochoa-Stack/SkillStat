from datetime import datetime, timedelta, timezone
from app.models.job_skill import JobSkill
from app.models.job import Job
from app.repositories.base_repository import BaseRepository
from app.extensions import db

class JobSkillRepository(BaseRepository):
    model = JobSkill

    @classmethod
    def get_active(cls, days: int = 30):
        # Filtramos por antigüedad de la vacante asociada para que demand_count refleje actividad reciente del mercado en vez de un acumulado historico que nunca puede bajar. Sin esto, growth_rate no podria detectar declive real de ninguna habilidad.
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return db.session.execute(
            db.select(JobSkill)
            .join(Job, Job.id == JobSkill.job_id)
            .filter(Job.created_at >= cutoff)
        ).scalars().all()
