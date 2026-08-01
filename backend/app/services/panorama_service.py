from app.repositories.skill_repository import SkillRepository
from app.repositories.city_repository import CityRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository

class PanoramaService:
    # Orquesta las consultas necesarias para la vista de comparacion, usando metodos batch para evitar el patron N+1 que antes generaba hasta 15 queries individuales para 5 habilidades.

    @classmethod
    def get_compare_data(cls, skill_ids: list[int]) -> dict:
        """
        Retorna dict con:
        - 'missing_ids': list[int] - ids solicitados que no existen
        - 'blocks': list[dict] - un bloque por skill_id válido, en el mismo orden que skill_ids, con la misma forma que el payload que get_compare ya arma hoy (skill_id, skill_name, demand_count, growth_rate, avg_salary, series). Si missing_ids no está vacío, blocks debe ser una lista vacía; el controlador decide si retorna 404, el servicio solo reporta qué falta. """
        skills = SkillRepository.get_by_ids(skill_ids)
        skills_by_id = {s.id: s for s in skills}
        missing_ids = [sid for sid in skill_ids if sid not in skills_by_id]

        if missing_ids:
            return {"missing_ids": missing_ids, "blocks": []}

        latest_snapshots = TrendSnapshotRepository.get_latest_by_skill_ids(skill_ids)
        latest_by_skill = {s.skill_id: s for s in latest_snapshots}

        all_snapshots = TrendSnapshotRepository.get_by_skill_ids(skill_ids)
        series_by_skill = {}
        for snap in all_snapshots:
            series_by_skill.setdefault(snap.skill_id, []).append(snap)

        blocks = []
        for sid in skill_ids:
            skill = skills_by_id[sid]
            latest = latest_by_skill.get(sid)
            series = series_by_skill.get(sid, [])
            blocks.append({
                "skill_id": skill.id,
                "skill_name": skill.name,
                "demand_count": latest.demand_count if latest else 0,
                "growth_rate": latest.growth_rate if latest else None,
                "avg_salary": latest.avg_salary if latest else None,
                "series": [
                    {"date": s.date, "demand_count": s.demand_count}
                    for s in series
                ],
            })

        return {"missing_ids": [], "blocks": blocks}

    @classmethod
    def get_all_skills(cls) -> list:
        return SkillRepository.get_all()

    @classmethod
    def get_catalogs_data(cls) -> dict:
        skills = SkillRepository.get_all()
        cities = CityRepository.get_all()
        return {
            "skills": [{"id": s.id, "name": s.name} for s in skills],
            "cities": [{"id": c.id, "name": c.name} for c in cities],
        }

    @classmethod
    def get_summary_data(cls) -> dict:
        data = TrendSnapshotRepository.get_summary_data()

        def build_skill_block(row):
            if not row:
                return None
            snapshot, skill_name = row
            return {
                "skill_id": snapshot.skill_id,
                "name": skill_name,
                "demand_count": snapshot.demand_count,
                "growth_rate": snapshot.growth_rate,
                "avg_salary": snapshot.avg_salary,
            }

        return {
            "total_jobs": data["total_jobs"],
            "total_skills_tracked": data["total_skills_tracked"],
            "total_companies": data["total_companies"],
            "top_emerging_skill": build_skill_block(data["top_emerging"]),
            "top_declining_skill": build_skill_block(data["top_declining"]),
            "last_updated": data["latest_date"],
        }

    @classmethod
    def get_top_skills_data(cls, limit: int) -> list:
        snapshots = TrendSnapshotRepository.get_top_skills(limit=limit)
        return [
            {
                "skill_id": s.skill_id,
                "name": s.skill.name if s.skill else None,
                "category": s.skill.category.name if s.skill and s.skill.category else None,
                "demand_count": s.demand_count,
                "growth_rate": s.growth_rate,
                "avg_salary": s.avg_salary,
            }
            for s in snapshots
        ]

    @classmethod
    def get_trends_data(cls, skill_id: int) -> dict | None:
        # Retorna None si el skill no existe; el controlador decide el 404.
        skill = SkillRepository.get_by_id(skill_id)
        if not skill:
            return None
        snapshots = TrendSnapshotRepository.get_by_skill_id(skill_id)
        return {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "series": [
                {"date": s.date, "demand_count": s.demand_count}
                for s in snapshots
            ],
        }

    @classmethod
    def get_geo_data(cls, skill_id: int | None, group_by: str) -> dict | tuple:
        """ Retorna ("NOT_FOUND", None) si skill_id fue dado pero no existe. Retorna dict normal en cualquier otro caso. La convención de retorno distinta a get_trends_data y get_salaries_data refleja que aquí skill_id es opcional; sin él, la respuesta es válida. """
        skill = None
        if skill_id is not None:
            skill = SkillRepository.get_by_id(skill_id)
            if not skill:
                return ("NOT_FOUND", None)
        rows = TrendSnapshotRepository.get_geo_distribution(skill_id=skill_id, group_by=group_by)
        distribution = []
        for row in rows:
            if group_by == "state":
                distribution.append({
                    "state": row.state,
                    "demand_count": row.total_demand,
                    "is_fallback": row.is_fallback,
                })
            else:
                distribution.append({
                    "city_id": row.city_id,
                    "city_name": row.city_name,
                    "state": row.state,
                    "demand_count": row.total_demand,
                })
        return {
            "skill_id": skill.id if skill else None,
            "skill_name": skill.name if skill else None,
            "distribution": distribution,
        }

    @classmethod
    def get_salaries_data(cls, skill_id: int) -> dict | None:
        # Retorna None si el skill no existe; el controlador decide el 404.
        skill = SkillRepository.get_by_id(skill_id)
        if not skill:
            return None
        stats = SkillRepository.get_salary_stats(skill_id)
        return {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "avg_salary_min": stats.avg_salary_min if stats else None,
            "avg_salary_max": stats.avg_salary_max if stats else None,
            "sample_size": stats.sample_size if stats else 0,
        }
