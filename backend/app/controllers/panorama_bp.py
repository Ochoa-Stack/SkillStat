from flask import Blueprint
from app.repositories.skill_repository import SkillRepository
from app.repositories.city_repository import CityRepository
from app.schemas.skill_schema import SkillResponseSchema
from app.schemas.panorama_schema import CatalogsResponseSchema
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
