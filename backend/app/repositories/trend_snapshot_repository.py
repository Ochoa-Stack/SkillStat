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
