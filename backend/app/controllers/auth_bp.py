from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from marshmallow import ValidationError
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.schemas.auth_schema import UserRegistrationSchema, UserLoginSchema, UserResponseSchema
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_account_repository import OAuthAccountRepository
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

    # Traducimos el DTO de entrada al modelo de dominio. Extraemos 'password' y lo inyectamos como 'password_hash' para que SQLAlchemy lo acepte.
    data["password_hash"] = hash_password(data.pop("password"))
    data["role"] = "REGISTERED"

    user = UserRepository.create(data)
    result = UserResponseSchema().dump(user)

    # Dejamos al usuario logueado de inmediato tras registrarse, en vez de obligarlo a escribir sus credenciales otra vez en una pantalla de login separada.
    tokens = generate_tokens(user_id=user.id, role=user.role)
    response, status_code = success_response(data=result, status_code=201)
    set_access_cookies(response, tokens["access_token"])
    return response, status_code

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
    user_data = UserResponseSchema().dump(user)

    # El token nunca viaja en el cuerpo JSON: si lo devolvieramos aqui, un script de XSS podria leerlo desde la respuesta del fetch aunque la cookie sea httpOnly, anulando la proteccion que buscamos.
    response, status_code = success_response(data=user_data, status_code=200)
    set_access_cookies(response, tokens["access_token"])
    return response, status_code


@auth_bp.route("/logout", methods=["POST"])
def logout():
    response, status_code = success_response(
        data={"message": "Sesión cerrada correctamente."}, status_code=200
    )
    unset_jwt_cookies(response)
    return response, status_code

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = UserRepository.get_by_id(int(user_id))
    
    if not user:
        return error_response(code="NOT_FOUND", message="Usuario no encontrado.", status_code=404)
        
    result = UserResponseSchema().dump(user)
    return success_response(data=result, status_code=200)


@auth_bp.route("/google", methods=["POST"])
def google_login():
    data = request.get_json() or {}
    credential = data.get("credential")

    if not credential:
        return error_response(
            code="VALIDATION_ERROR",
            message="El token de Google es obligatorio.",
            status_code=422,
        )

    try:
        idinfo = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            current_app.config["GOOGLE_CLIENT_ID"],
        )
    except ValueError:
        return error_response(
            code="TOKEN_INVALID",
            message="El token de Google no es válido.",
            status_code=401,
        )

    # Solo vinculamos automaticamente con una cuenta existente si Google ya verifico que el usuario controla ese correo; sin esto, alguien podria reclamar la cuenta de otra persona con solo conocer su email.
    email_verified = str(idinfo.get("email_verified", "")).lower() == "true"
    if not email_verified:
        return error_response(
            code="EMAIL_NOT_VERIFIED",
            message="El correo de Google no está verificado.",
            status_code=401,
        )

    google_user_id = idinfo["sub"]
    email = idinfo["email"].lower().strip()

    oauth_account = OAuthAccountRepository.get_by_provider_identity(
        "google", google_user_id
    )

    if oauth_account:
        user = UserRepository.get_by_id(oauth_account.user_id)
        if not user:
            return error_response(
                code="NOT_FOUND",
                message="La cuenta vinculada ya no existe.",
                status_code=404,
            )
    else:
        user = UserRepository.get_by_email(email)
        if not user:
            # Primera vez que vemos este correo: la cuenta nace sin password_hash porque este usuario siempre entrara por Google.
            user = UserRepository.create({
                "email": email,
                "first_name": idinfo.get("given_name", "Usuario"),
                "last_name": idinfo.get("family_name", "Google"),
                "role": "REGISTERED",
            })

        # Vinculamos esta identidad de Google a la cuenta, nueva o existente; si ya habia una cuenta con este correo via registro normal, queda vinculada automaticamente.
        oauth_link = OAuthAccountRepository.create({
            "user_id": user.id,
            "provider": "google",
            "provider_user_id": google_user_id,
        })
        if not oauth_link:
            return error_response(
                code="INTERNAL_ERROR",
                message="No se pudo vincular la cuenta de Google.",
                status_code=500,
            )

    tokens = generate_tokens(user_id=user.id, role=user.role)
    result = UserResponseSchema().dump(user)

    response, status_code = success_response(data=result, status_code=200)
    set_access_cookies(response, tokens["access_token"])
    return response, status_code
