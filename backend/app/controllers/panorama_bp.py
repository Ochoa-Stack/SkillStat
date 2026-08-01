from flask import Blueprint, request
from app.services.panorama_service import PanoramaService
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
    skills = PanoramaService.get_all_skills()
    result = SkillResponseSchema(many=True).dump(skills)
    return success_response(data=result, status_code=200)

@panorama_bp.route("/catalogs", methods=["GET"])
def get_catalogs():
    payload = PanoramaService.get_catalogs_data()
    result = CatalogsResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)

@panorama_bp.route("/summary", methods=["GET"])
def get_summary():
    payload = PanoramaService.get_summary_data()
    result = SummaryResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)

@panorama_bp.route("/skills/top", methods=["GET"])
def get_top_skills():
    limit = request.args.get("limit", default=10, type=int)
    # Acotamos el limite para evitar que un valor arbitrario en la query fuerce una consulta desproporcionada contra la base de datos — validacion de entrada HTTP, no logica de negocio.
    limit = max(1, min(limit, 50))
    payload = PanoramaService.get_top_skills_data(limit=limit)
    result = SkillTrendSchema(many=True).dump(payload)
    return success_response(data=result, status_code=200)

@panorama_bp.route("/trends", methods=["GET"])
def get_trends():
    skill_id = request.args.get("skill_id", type=int)

    if not skill_id:
        return error_response(
            code="VALIDATION_ERROR",
            message="El parametro skill_id es obligatorio.",
            status_code=422,
        )

    payload = PanoramaService.get_trends_data(skill_id)
    if payload is None:
        return error_response(
            code="NOT_FOUND",
            message="La habilidad solicitada no existe.",
            status_code=404,
        )

    result = TrendsResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)

@panorama_bp.route("/geo", methods=["GET"])
def get_geo():
    skill_id = request.args.get("skill_id", type=int)
    group_by = request.args.get("group_by", default="city", type=str)

    if group_by not in ["city", "state"]:
        return error_response(
            code="VALIDATION_ERROR",
            message="El parametro group_by debe ser 'city' o 'state'.",
            status_code=422,
        )

    payload = PanoramaService.get_geo_data(skill_id=skill_id, group_by=group_by)
    if isinstance(payload, tuple) and payload[0] == "NOT_FOUND":
        return error_response(
            code="NOT_FOUND",
            message="La habilidad solicitada no existe.",
            status_code=404,
        )

    result = GeoResponseSchema().dump(payload)
    return success_response(data=result, status_code=200)

@panorama_bp.route("/salaries", methods=["GET"])
def get_salaries():
    skill_id = request.args.get("skill_id", type=int)

    if not skill_id:
        return error_response(
            code="VALIDATION_ERROR",
            message="El parametro skill_id es obligatorio.",
            status_code=422,
        )

    payload = PanoramaService.get_salaries_data(skill_id)
    if payload is None:
        return error_response(
            code="NOT_FOUND",
            message="La habilidad solicitada no existe.",
            status_code=404,
        )

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

    data = PanoramaService.get_compare_data(skill_ids)

    if data["missing_ids"]:
        return error_response(
            code="NOT_FOUND",
            message=f"Las siguientes habilidades no existen: {data['missing_ids']}.",
            status_code=404,
        )

    blocks = data["blocks"]

    result = CompareResponseSchema().dump({"skills": blocks})
    return success_response(data=result, status_code=200)
