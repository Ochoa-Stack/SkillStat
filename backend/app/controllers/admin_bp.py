import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.services.ingestion_service import IngestionService
from app.services.backup_service import BackupService
from app.repositories.backup_repository import BackupRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_schema import UserRoleSchema, UserStatusSchema
from app.utils.response import success_response, error_response
from app.utils.decorators import role_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/ingest", methods=["POST"])
@jwt_required()
@role_required("ADMIN")
def trigger_ingestion():
    payload = request.get_json() or {}
    pages = payload.get("pages", 1)

    # Mandamos llamar al orquestador principal de la Capa de Servicios
    stats = IngestionService.run_ingestion(pages=pages)

    return success_response(data=stats, status_code=200)


@admin_bp.route("/backup", methods=["POST"])
@jwt_required()
@role_required("ADMIN")
def trigger_backup():
    user_id = int(get_jwt_identity())

    # Delegamos la ejecución del dump físico al servicio operativo
    result = BackupService.execute_database_backup(requested_by=user_id)

    return success_response(data=result, status_code=200)


@admin_bp.route("/backups", methods=["GET"])
@jwt_required()
@role_required("ADMIN")
def list_backups():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    if per_page < 1 or per_page > 100:
        return error_response(
            code="VALIDATION_ERROR",
            message="per_page debe estar entre 1 y 100.",
            status_code=422,
        )

    items, total = BackupRepository.get_paginated(page=page, per_page=per_page)

    result = {
        "items": [
            {
                "id": b.id,
                "filename": b.filename,
                "storage_url": b.storage_url,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "user_id": b.user_id,
                "user_email": email,
            }
            for b, email in items
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        # División entera con techo; si no hay registros, devolvemos 0 en vez de -1 por el offset de la resta
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
    }

    return success_response(data=result, status_code=200)


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@role_required("ADMIN")
def list_users():

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    if per_page < 1 or per_page > 100:
        return error_response(
            code="VALIDATION_ERROR",
            message="per_page debe estar entre 1 y 100.",
            status_code=422,
        )

    items, total = UserRepository.get_paginated(page=page, per_page=per_page)

    result = {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in items
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
    }

    return success_response(data=result, status_code=200)


@admin_bp.route("/users/<int:user_id>/role", methods=["PATCH"])
@jwt_required()
@role_required("ADMIN")
def update_user_role(user_id):
    actor_id = int(get_jwt_identity())
    try:
        payload = UserRoleSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(
            code="VALIDATION_ERROR",
            message=err.messages,
            status_code=422,
        )

    target = UserRepository.get_by_id(user_id)
    if not target:
        return error_response(
            code="NOT_FOUND",
            message="Usuario no encontrado.",
            status_code=404,
        )

    new_role = payload["role"]
    # Si el actor se esta auto-modificando y la operacion lo saca de ADMIN, protegemos contra dejar el sistema sin ningun admin activo.
    if target.id == actor_id and target.role == "ADMIN" and new_role != "ADMIN":
        if UserRepository.count_active_admins() <= 1:
            return error_response(
                code="LAST_ADMIN_PROTECTED",
                message="No puedes quitarte el rol de ADMIN: eres el unico administrador activo.",
                status_code=403,
            )

    previous_role = target.role
    target.role = new_role
    saved = UserRepository.save(target)
    if not saved:
        return error_response(
            code="INTERNAL_ERROR",
            message="No se pudo actualizar el rol.",
            status_code=500,
        )

    logger.info(
        "Cambio de rol: admin %s cambio a usuario %s (%s) de %s a %s.",
        actor_id, target.id, target.email, previous_role, new_role
    )
    return success_response(
        data={"id": target.id, "role": target.role}, status_code=200
    )


@admin_bp.route("/users/<int:user_id>/status", methods=["PATCH"])
@jwt_required()
@role_required("ADMIN")
def update_user_status(user_id):
    actor_id = int(get_jwt_identity())
    try:
        payload = UserStatusSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(
            code="VALIDATION_ERROR",
            message=err.messages,
            status_code=422,
        )

    target = UserRepository.get_by_id(user_id)
    if not target:
        return error_response(
            code="NOT_FOUND",
            message="Usuario no encontrado.",
            status_code=404,
        )

    new_status = payload["is_active"]
    # Misma proteccion de ultimo-admin, aplicada a desactivacion en vez de cambio de rol.
    if target.id == actor_id and target.role == "ADMIN" and new_status is False:
        if UserRepository.count_active_admins() <= 1:
            return error_response(
                code="LAST_ADMIN_PROTECTED",
                message="No puedes desactivar tu cuenta: eres el unico administrador activo.",
                status_code=403,
            )

    previous_status = target.is_active
    target.is_active = new_status
    saved = UserRepository.save(target)
    if not saved:
        return error_response(
            code="INTERNAL_ERROR",
            message="No se pudo actualizar el estado.",
            status_code=500,
        )

    logger.info(
        "Cambio de estado: admin %s cambio a usuario %s (%s) de is_active=%s a %s.",
        actor_id, target.id, target.email, previous_status, new_status
    )
    return success_response(
        data={"id": target.id, "is_active": target.is_active}, status_code=200
    )
