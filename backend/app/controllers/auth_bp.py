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
    try:
        data = UserRegistrationSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    if UserRepository.get_by_email(data["email"]):
        return error_response(code="CONFLICT", message="El correo ya está registrado.", status_code=409)

    # Traducimos el DTO de entrada al modelo de dominio.
    # Extraemos 'password' y lo inyectamos como 'password_hash' para que SQLAlchemy lo acepte.
    data["password_hash"] = hash_password(data.pop("password"))
    data["role"] = "REGISTERED"
    
    user = UserRepository.create(data)

    result = UserResponseSchema().dump(user)
    return success_response(data=result, status_code=201)

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = UserLoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    user = UserRepository.get_by_email(data["email"])
    
    # Comparamos contra el atributo real del modelo de base de datos (password_hash)
    if not user or not verify_password(data["password"], user.password_hash):
        return error_response(code="UNAUTHORIZED", message="Credenciales incorrectas.", status_code=401)

    tokens = generate_tokens(user_id=user.id, role=user.role)
    return success_response(data=tokens, status_code=200)

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = UserRepository.get_by_id(int(user_id))
    
    if not user:
        return error_response(code="NOT_FOUND", message="Usuario no encontrado.", status_code=404)
        
    result = UserResponseSchema().dump(user)
    return success_response(data=result, status_code=200)
