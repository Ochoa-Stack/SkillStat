from flask import Blueprint
from app.repositories.skill_repository import SkillRepository
from app.schemas.skill_schema import SkillResponseSchema
from app.utils.response import success_response

panorama_bp = Blueprint("panorama_bp", __name__)

@panorama_bp.route("/skills", methods=["GET"])
def get_skills():
    # Exponemos el catálogo estático aplicando el esquema de solo lectura para alimentar los selectores de la interfaz sin filtrar metadatos internos.
    skills = SkillRepository.get_all()
    result = SkillResponseSchema(many=True).dump(skills)
    return success_response(data=result, status_code=200)
