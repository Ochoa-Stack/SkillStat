import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.repositories.skill_repository import SkillRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_skill_repository import UserSkillRepository
from app.services.profile_service import ProfileService
from app.schemas.profile_schema import (
    UpdateProfileSchema,
    AddSkillSchema,
    ChangePasswordSchema,
)
from app.utils.decorators import role_required
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)

profile_bp = Blueprint("profile_bp", __name__)


@profile_bp.route("/me", methods=["GET"])
@jwt_required()
@role_required("REGISTERED", "ADMIN")
def get_profile():
    user_id = int(get_jwt_identity())
    user = UserRepository.get_by_id(user_id)
    if not user:
        return error_response(code="NOT_FOUND", message="Usuario no encontrado.", status_code=404)

    return success_response(data={
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "intent": user.intent,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


@profile_bp.route("/me", methods=["PATCH"])
@jwt_required()
@role_required("REGISTERED", "ADMIN")
def update_profile():
    try:
        data = UpdateProfileSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    user_id = int(get_jwt_identity())
    user = ProfileService.update_profile(user_id, data)
    if not user:
        return error_response(code="NOT_FOUND", message="Usuario no encontrado.", status_code=404)

    return success_response(data={
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "intent": user.intent,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


@profile_bp.route("/skill-gap", methods=["GET"])
@jwt_required()
@role_required("REGISTERED", "ADMIN")
def get_skill_gap():
    user_id = int(get_jwt_identity())
    result = ProfileService.get_skill_gap(user_id)
    return success_response(data=result)


@profile_bp.route("/skills", methods=["POST"])
@jwt_required()
@role_required("REGISTERED", "ADMIN")
def add_skill():
    try:
        data = AddSkillSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    skill_id = data["skill_id"]
    skill = SkillRepository.get_by_id(skill_id)
    if not skill:
        return error_response(code="SKILL_NOT_FOUND", message="La habilidad no existe.", status_code=404)

    user_id = int(get_jwt_identity())
    UserSkillRepository.add_skill(user_id, skill_id)
    return success_response(data={"skill_id": skill_id, "name": skill.name}, status_code=201)


@profile_bp.route("/skills/<int:skill_id>", methods=["DELETE"])
@jwt_required()
@role_required("REGISTERED", "ADMIN")
def remove_skill(skill_id: int):
    user_id = int(get_jwt_identity())
    # La eliminacion es idempotente dado qué responde 200 tanto si existia la relacion como si no.
    UserSkillRepository.remove_skill(user_id, skill_id)
    return success_response(data={"message": "Habilidad eliminada del perfil."})


@profile_bp.route("/change-password", methods=["POST"])
@jwt_required()
@role_required("REGISTERED", "ADMIN")
def change_password():
    try:
        data = ChangePasswordSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    user_id = int(get_jwt_identity())
    try:
        ProfileService.change_password(
            user_id,
            data["current_password"],
            data["new_password"],
        )
    except ValueError as e:
        if str(e) == "INVALID_CREDENTIALS":
            return error_response(
                code="INVALID_CREDENTIALS",
                message="La contrasena actual es incorrecta.",
                status_code=400,
            )
        raise

    return success_response(data={"message": "Contrasena actualizada correctamente."})
