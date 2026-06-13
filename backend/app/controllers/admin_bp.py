from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.services.ingestion_service import IngestionService
from app.services.backup_service import BackupService
from app.utils.response import success_response, error_response

admin_bp = Blueprint("admin_bp", __name__)

def admin_required():
    # Helper local para evaluar los claims del JWT inyectados durante el login.
    # Garantiza que incluso un token válido sea rechazado si carece del privilegio necesario.
    claims = get_jwt()
    return claims.get("role") == "ADMIN"

@admin_bp.route("/ingest", methods=["POST"])
@jwt_required()
def trigger_ingestion():
    if not admin_required():
        return error_response(code="FORBIDDEN", message="Privilegios de administrador requeridos.", status_code=403)
        
    payload = request.get_json() or {}
    pages = payload.get("pages", 1)
    
    # Invocamos el orquestador principal de la Capa de Servicios
    stats = IngestionService.run_ingestion(pages=pages)
    
    return success_response(data=stats, status_code=200)

@admin_bp.route("/backup", methods=["POST"])
@jwt_required()
def trigger_backup():
    if not admin_required():
        return error_response(code="FORBIDDEN", message="Privilegios de administrador requeridos.", status_code=403)
        
    user_id = int(get_jwt_identity())
    
    # Delegamos la ejecución del dump físico al servicio operativo
    result = BackupService.execute_database_backup(requested_by=user_id)
    
    return success_response(data=result, status_code=200)
