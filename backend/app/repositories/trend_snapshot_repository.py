from sqlalchemy import desc
from app.repositories.base_repository import BaseRepository
from app.models.trend_snapshot import TrendSnapshot
from app.extensions import db


class TrendSnapshotRepository(BaseRepository):
    model = TrendSnapshot

    @classmethod
    def get_latest_by_skill(cls, skill_id: int):
        return db.session.execute(
            db.select(TrendSnapshot)
            .filter_by(skill_id=skill_id)
            .order_by(desc(TrendSnapshot.date))
            .limit(1)
        ).scalar_one_or_none()

    @classmethod
    def get_top_skills(cls, limit: int = 10) -> list:
        # Traemos los snapshots mas recientes ordenados por demanda para construir el ranking del endpoint skills/top.
        return db.session.execute(
            db.select(TrendSnapshot)
            .order_by(desc(TrendSnapshot.demand_count))
            .limit(limit)
        ).scalars().all()

    @classmethod
    def get_by_skill_id(cls, skill_id: int) -> list:
        return db.session.execute(
            db.select(TrendSnapshot)
            .filter_by(skill_id=skill_id)
            .order_by(TrendSnapshot.date)
        ).scalars().all()

    @classmethod
    def get_by_city_id(cls, city_id: int) -> list:
        return db.session.execute(
            db.select(TrendSnapshot)
            .filter_by(city_id=city_id)
            .order_by(desc(TrendSnapshot.demand_count))
        ).scalars().all()

    @classmethod
    def get_all_latest(cls) -> list:
        # Subconsulta para obtener la fecha mas reciente por skill+city.
        # Usamos esto para que summary y catalogs trabajen sobre datos actuales y no sobre historico acumulado.
        from sqlalchemy import func
        subq = db.session.execute(
            db.select(
                TrendSnapshot.skill_id,
                TrendSnapshot.city_id,
                func.max(TrendSnapshot.date).label("max_date")
            ).group_by(TrendSnapshot.skill_id, TrendSnapshot.city_id)
        ).all()
        return subq

    @classmethod
    def get_salary_by_skill(cls, skill_id: int):
        from sqlalchemy import func
        return db.session.execute(
            db.select(
                func.avg(TrendSnapshot.avg_salary).label("avg_salary")
            ).filter_by(skill_id=skill_id)
        ).scalar_one_or_none()

    @classmethod
    def get_summary_data(cls):
        from sqlalchemy import func
        from app.models.job import Job
        from app.models.skill import Skill

        total_jobs = db.session.execute(
            db.select(func.count(Job.id))
        ).scalar_one()

        total_skills_tracked = db.session.execute(
            db.select(func.count(func.distinct(TrendSnapshot.skill_id)))
        ).scalar_one()

        latest_date = db.session.execute(
            db.select(func.max(TrendSnapshot.date))
        ).scalar_one_or_none()

        # Traemos el snapshot mas reciente por skill para identificar cual tiene mayor y menor demanda actual.
        top_emerging = db.session.execute(
            db.select(TrendSnapshot, Skill.name)
            .join(Skill, Skill.id == TrendSnapshot.skill_id)
            .order_by(db.desc(TrendSnapshot.demand_count))
            .limit(1)
        ).first()

        top_declining = db.session.execute(
            db.select(TrendSnapshot, Skill.name)
            .join(Skill, Skill.id == TrendSnapshot.skill_id)
            .order_by(TrendSnapshot.demand_count)
            .limit(1)
        ).first()

        return {
            "total_jobs": total_jobs,
            "total_skills_tracked": total_skills_tracked,
            "latest_date": latest_date,
            "top_emerging": top_emerging,
            "top_declining": top_declining,
        }

    @classmethod
    def get_geo_distribution(cls, skill_id: int = None) -> list:
        from sqlalchemy import func
        from app.models.city import City

        # Sumamos demand_count por ciudad. Si se filtra por skill_id
        # la suma queda acotada a esa habilidad especifica, de lo
        # contrario agregamos la demanda total de todas las habilidades.
        query = (
            db.select(
                City.id.label("city_id"),
                City.name.label("city_name"),
                func.sum(TrendSnapshot.demand_count).label("total_demand"),
            )
            .join(City, City.id == TrendSnapshot.city_id)
            .group_by(City.id, City.name)
            .order_by(func.sum(TrendSnapshot.demand_count).desc())
        )

        if skill_id is not None:
            query = query.filter(TrendSnapshot.skill_id == skill_id)

        return db.session.execute(query).all()
