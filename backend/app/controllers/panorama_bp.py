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
    SalaryResponseSchema,
    CompareResponseSchema,
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
    # KPIs globales que alimentan las tarjetas superiores del Panorama
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
        "total_companies": data["total_companies"],
        "top_emerging_skill": build_skill_block(data["top_emerging"]),
        "top_declining_skill": build_skill_block(data["top_declining"]),
        "last_updated": data["latest_date"],
    }

    result = SummaryResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/skills/top", methods=["GET"])
def get_top_skills():
    # Ranking de habilidades por demanda actual. El frontend lo usa para la grafica de barras principal del Panorama
    limit = request.args.get("limit", default=10, type=int)
    # Acotamos el limite para evitar que un valor arbitrario en la query fuerce una consulta desproporcionada contra la base de datos
    limit = max(1, min(limit, 50))

    snapshots = TrendSnapshotRepository.get_top_skills(limit=limit)

    payload = [
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

    result = SkillTrendSchema(many=True).dump(payload)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/trends", methods=["GET"])
def get_trends():
    # Serie temporal de demanda para una habilidad especifica. El frontend la usa para la grafica de lineas de evolucion
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
    group_by = request.args.get("group_by", default="city", type=str)

    if group_by not in ["city", "state"]:
        return error_response(
            code="VALIDATION_ERROR",
            message="El parametro group_by debe ser 'city' o 'state'.",
            status_code=422,
        )

    skill = None
    if skill_id is not None:
        skill = SkillRepository.get_by_id(skill_id)
        if not skill:
            return error_response(
                code="NOT_FOUND",
                message="La habilidad solicitada no existe.",
                status_code=404,
            )

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

    payload = {
        "skill_id": skill.id if skill else None,
        "skill_name": skill.name if skill else None,
        "distribution": distribution,
    }

    result = GeoResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/salaries", methods=["GET"])
def get_salaries():
    # Cruce de habilidad contra rango salarial promedio. Requiere skill_id porque el calculo es por habilidad, no agregable globalmente sin perder sentido.
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

    stats = SkillRepository.get_salary_stats(skill_id)

    payload = {
        "skill_id": skill.id,
        "skill_name": skill.name,
        "avg_salary_min": stats.avg_salary_min if stats else None,
        "avg_salary_max": stats.avg_salary_max if stats else None,
        "sample_size": stats.sample_size if stats else 0,
    }

    result = SalaryResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)


@panorama_bp.route("/compare", methods=["GET"])
def get_compare():
    # Comparacion lado a lado de multiples habilidades. El frontend la usa para la vista de comparar.html con grafica multi-linea
    raw_param = request.args.get("skill_ids", default="", type=str)

    if not raw_param.strip():
        return error_response(
            code="VALIDATION_ERROR",
            message="El parametro skill_ids es obligatorio.",
            status_code=422,
        )

    try:
        skill_ids = [int(s.strip()) for s in raw_param.split(",") if s.strip()]
    except ValueError:
        return error_response(
            code="VALIDATION_ERROR",
            message="skill_ids debe ser una lista de enteros separados por comas.",
            status_code=422,
        )

    # Acotamos entre 2 y 5 habilidades, puesto que comparar una sola no tiene sentido funcional, y mas de 5 degrada la lectura de la grafica
    if len(skill_ids) < 2 or len(skill_ids) > 5:
        return error_response(
            code="VALIDATION_ERROR",
            message="skill_ids debe contener entre 2 y 5 habilidades.",
            status_code=422,
        )

    skills_map = {}
    missing_ids = []
    for sid in skill_ids:
        skill = SkillRepository.get_by_id(sid)
        if skill:
            skills_map[sid] = skill
        else:
            missing_ids.append(sid)

    if missing_ids:
        return error_response(
            code="NOT_FOUND",
            message=f"Las siguientes habilidades no existen: {missing_ids}.",
            status_code=404,
        )

    blocks = []
    for sid in skill_ids:
        skill = skills_map[sid]
        latest = TrendSnapshotRepository.get_latest_by_skill(sid)
        series_snapshots = TrendSnapshotRepository.get_by_skill_id(sid)

        blocks.append({
            "skill_id": skill.id,
            "skill_name": skill.name,
            "demand_count": latest.demand_count if latest else 0,
            "avg_salary": latest.avg_salary if latest else None,
            "series": [
                {"date": s.date, "demand_count": s.demand_count}
                for s in series_snapshots
            ],
        })

    result = CompareResponseSchema().dump({"skills": blocks})
    return success_response(data=result, status_code=200)
