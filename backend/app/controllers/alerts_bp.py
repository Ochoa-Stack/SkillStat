from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.schemas.alert_schema import AlertRequestSchema, AlertResponseSchema
from app.repositories.alert_repository import AlertRepository
from app.utils.response import success_response, error_response

alerts_bp = Blueprint("alerts_bp", __name__)

@alerts_bp.route("/", methods=["POST"])
@jwt_required()
def create_alert():
    try:
        data = AlertRequestSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    user_id = get_jwt_identity()
    
    # Forzamos el ID extraído del token criptográfico sobre la carga de datos para erradicar ataques de asignación cruzada o escalamiento horizontal.
    data["user_id"] = int(user_id)

    alert = AlertRepository.create(data)
    result = AlertResponseSchema().dump(alert)
    return success_response(data=result, status_code=201)

@alerts_bp.route("/", methods=["GET"])
@jwt_required()
def get_alerts():
    user_id = int(get_jwt_identity())
    
    # Filtramos en memoria para garantizar que el usuario actual no tenga visibilidad sobre configuraciones ajenas.
    all_alerts = AlertRepository.get_all()
    user_alerts = [a for a in all_alerts if a.user_id == user_id]
    
    result = AlertResponseSchema(many=True).dump(user_alerts)
    return success_response(data=result, status_code=200)

@alerts_bp.route("/<int:alert_id>", methods=["DELETE"])
@jwt_required()
def delete_alert(alert_id):
    user_id = int(get_jwt_identity())
    alert = AlertRepository.get_by_id(alert_id)
    
    if not alert or alert.user_id != user_id:
        # Devolvemos un estado no encontrado general en lugar de un error de acceso para no confirmar la existencia de IDs reales ante un escaneo malicioso.
        return error_response(code="NOT_FOUND", message="Alerta no encontrada.", status_code=404)
        
    AlertRepository.delete(alert_id)
    return success_response(data={"deleted": True}, status_code=200)
