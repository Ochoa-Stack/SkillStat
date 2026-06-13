from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.schemas.auth_schema import UserRegistrationSchema, UserLoginSchema, UserResponseSchema
from app.repositories.user_repository import UserRepository
from app.utils.hash import hash_password, verify_password
from app.utils.security import generate_tokens
from app.utils.response import success_response, error_response

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    # Validación de Entrada
    try:
        data = UserRegistrationSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    # Verificación de conflictos
    if UserRepository.get_by_email(data["email"]):
        return error_response(code="CONFLICT", message="El correo ya está registrado.", status_code=409)

    # Preparación y persistencia
    data["password"] = hash_password(data["password"])
    data["role"] = "REGISTERED"
    
    user = UserRepository.create(data)

    # Validación de Salida
    result = UserResponseSchema().dump(user)
    return success_response(data=result, status_code=201)

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = UserLoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    user = UserRepository.get_by_email(data["email"])
    if not user or not verify_password(data["password"], user.password):
        return error_response(code="UNAUTHORIZED", message="Credenciales incorrectas.", status_code=401)

    # Generación de token JWT con rol inyectado
    tokens = generate_tokens(user_id=user.id, role=user.role)
    return success_response(data=tokens, status_code=200)

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    # Extraemos el ID del usuario del token JWT validado por la extensión
    user_id = get_jwt_identity()
    user = UserRepository.get_by_id(int(user_id))
    
    if not user:
        return error_response(code="NOT_FOUND", message="Usuario no encontrado.", status_code=404)
        
    result = UserResponseSchema().dump(user)
    return success_response(data=result, status_code=200)
