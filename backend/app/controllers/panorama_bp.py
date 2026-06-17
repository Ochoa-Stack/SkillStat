from flask import Blueprint
from app.repositories.skill_repository import SkillRepository
from app.repositories.city_repository import CityRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.schemas.skill_schema import SkillResponseSchema
from app.schemas.panorama_schema import CatalogsResponseSchema, SummaryResponseSchema
from app.utils.response import success_response

panorama_bp = Blueprint("panorama_bp", __name__)


@panorama_bp.route("/skills", methods=["GET"])
def get_skills():
    # Exponemos el catalogo estatico aplicando el esquema de solo lectura para alimentar los selectores de la interfaz sin filtrar metadatos internos.
    skills = SkillRepository.get_all()
    result = SkillResponseSchema(many=True).dump(skills)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/catalogs", methods=["GET"])
def get_catalogs():
    # Endpoint ligero pensado para poblar selectores del frontend.
    # Devolvemos id+name unicamente, sin metricas, para minimizar el payload en una ruta que probablemente se llama una sola vez por sesion.
    skills = SkillRepository.get_all()
    cities = CityRepository.get_all()

    payload = {
        "skills": [{"id": s.id, "name": s.name} for s in skills],
        "cities": [{"id": c.id, "name": c.name} for c in cities],
    }

    result = CatalogsResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/summary", methods=["GET"])
def get_summary():
    # KPIs globales que alimentan las tarjetas superiores del Panorama.
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

    payload = {
        "total_jobs": data["total_jobs"],
        "total_skills_tracked": data["total_skills_tracked"],
        "top_emerging_skill": build_skill_block(data["top_emerging"]),
        "top_declining_skill": build_skill_block(data["top_declining"]),
        "last_updated": data["latest_date"],
    }

    result = SummaryResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)
