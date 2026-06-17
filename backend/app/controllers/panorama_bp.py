from flask import Blueprint, request
from app.repositories.skill_repository import SkillRepository
from app.repositories.city_repository import CityRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.schemas.skill_schema import SkillResponseSchema
from app.schemas.panorama_schema import (
    CatalogsResponseSchema,
    SummaryResponseSchema,
    SkillTrendSchema,
    TrendsResponseSchema,
    GeoResponseSchema,
)
from app.utils.response import success_response, error_response

panorama_bp = Blueprint("panorama_bp", __name__)


@panorama_bp.route("/skills", methods=["GET"])
def get_skills():
    # Exponemos el catalogo estatico aplicando el esquema de solo lectura para alimentar los selectores de la interfaz sin filtrar metadatos internos.
    skills = SkillRepository.get_all()
    result = SkillResponseSchema(many=True).dump(skills)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/catalogs", methods=["GET"])
def get_catalogs():
    # Endpoint ligero pensado para poblar selectores del frontend. Devolvemos id+name unicamente, sin metricas, para minimizar el payload en una ruta que probablemente se llama una sola vez por sesion.
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


@panorama_bp.route("/skills/top", methods=["GET"])
def get_top_skills():
    # Ranking de habilidades por demanda actual. El frontend lo usa para la grafica de barras principal del Panorama.
    limit = request.args.get("limit", default=10, type=int)
    # Acotamos el limite para evitar que un valor arbitrario en la query fuerce una consulta desproporcionada contra la base de datos.
    limit = max(1, min(limit, 50))

    snapshots = TrendSnapshotRepository.get_top_skills(limit=limit)

    payload = [
        {
            "skill_id": s.skill_id,
            "name": s.skill.name if s.skill else None,
            "demand_count": s.demand_count,
            "growth_rate": s.growth_rate,
            "avg_salary": s.avg_salary,
        }
        for s in snapshots
    ]

    result = SkillTrendSchema(many=True).dump(payload)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/trends", methods=["GET"])
def get_trends():
    # Serie temporal de demanda para una habilidad especifica. El frontend la usa para la grafica de lineas de evolucion.
    skill_id = request.args.get("skill_id", type=int)

    if not skill_id:
        return error_response(
            code="VALIDATION_ERROR",
            message="El parametro skill_id es obligatorio.",
            status_code=422,
        )

    skill = SkillRepository.get_by_id(skill_id)
    if not skill:
        return error_response(
            code="NOT_FOUND",
            message="La habilidad solicitada no existe.",
            status_code=404,
        )

    snapshots = TrendSnapshotRepository.get_by_skill_id(skill_id)

    payload = {
        "skill_id": skill.id,
        "skill_name": skill.name,
        "series": [
            {"date": s.date, "demand_count": s.demand_count}
            for s in snapshots
        ],
    }

    result = TrendsResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/geo", methods=["GET"])
def get_geo():
    # Distribucion geografica de demanda. Si se filtra por skill_id devolvemos la distribucion de esa habilidad especifica, de lo contrario la demanda total agregada por ciudad.
    skill_id = request.args.get("skill_id", type=int)

    skill = None
    if skill_id is not None:
        skill = SkillRepository.get_by_id(skill_id)
        if not skill:
            return error_response(
                code="NOT_FOUND",
                message="La habilidad solicitada no existe.",
                status_code=404,
            )

    rows = TrendSnapshotRepository.get_geo_distribution(skill_id=skill_id)

    payload = {
        "skill_id": skill.id if skill else None,
        "skill_name": skill.name if skill else None,
        "distribution": [
            {
                "city_id": row.city_id,
                "city_name": row.city_name,
                "demand_count": row.total_demand,
            }
            for row in rows
        ],
    }

    result = GeoResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)
