from app.repositories.skill_repository import SkillRepository
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
