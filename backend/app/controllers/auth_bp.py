import secrets
import hashlib
import logging
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from marshmallow import ValidationError
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.schemas.auth_schema import (
    UserRegistrationSchema,
    UserLoginSchema,
    UserResponseSchema,
    ForgotPasswordSchema,
    EmailOnlySchema,
    ResetPasswordSchema,
)
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_account_repository import OAuthAccountRepository
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.email_verification_token_repository import EmailVerificationTokenRepository
from app.utils.hash import hash_password, verify_password
from app.utils.security import generate_tokens
from app.utils.response import success_response, error_response
from app.utils.errors import AppError
from app.extensions import limiter

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    try:
        data = UserRegistrationSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    if UserRepository.get_by_email(data["email"]):
        return error_response(code="CONFLICT", message="El correo ya está registrado.", status_code=409)

    data["password_hash"] = hash_password(data.pop("password"))
    data["role"] = "REGISTERED"
    # Marcamos el instante de creación de contraseña para que el blocklist callback pueda invalidar sesiones anteriores si la contraseña cambia.
    data["password_changed_at"] = datetime.now(timezone.utc)

    user = UserRepository.create(data)

    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    EmailVerificationTokenRepository.create({
        "user_id": user.id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    })

    from app.services.email_service import send_verification_email, EmailDeliveryError, build_verification_link
    try:
        logger.info(f"[DEV] Verification link para {user.email}: {build_verification_link(plain_token)}")
        send_verification_email(user.email, plain_token)
        return success_response(data={"message": "Cuenta creada. Revisa tu correo para verificarla."}, status_code=201)
    except EmailDeliveryError:
        return success_response(data={"message": "Cuenta creada pero no pudimos enviar el correo. Intenta reenviarlo."}, status_code=201)

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per 15 minutes")
def login():
    try:
        data = UserLoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    user = UserRepository.get_by_email(data["email"])

    if not user or user.password_hash is None or not verify_password(data["password"], user.password_hash):
        return error_response(code="UNAUTHORIZED", message="Credenciales incorrectas.", status_code=401)

    if user.email_verified_at is None:
        return error_response(code="EMAIL_NOT_VERIFIED", message="Verifica tu correo antes de iniciar sesión.", status_code=403)

    tokens = generate_tokens(user_id=user.id, role=user.role)
    user_data = UserResponseSchema().dump(user)

    # El token nunca viaja en el cuerpo JSON ya que si lo devolvieramos aqui, un script de XSS podria leerlo desde la respuesta del fetch aunque la cookie sea httpOnly, anulando la proteccion que buscamos.
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

    # Solo vinculamos automaticamente con una cuenta existente si Google ya verifico que el usuario controla ese correo, sin esto, alguien podria reclamar la cuenta de otra persona con solo conocer su email.
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
            # Si es la primera vez que vemos este correo, la cuenta nace sin password_hash porque este usuario siempre entrara por Google.
            user = UserRepository.create({
                "email": email,
                "first_name": idinfo.get("given_name", "Usuario"),
                "last_name": idinfo.get("family_name", "Google"),
                "role": "REGISTERED",
                "email_verified_at": datetime.now(timezone.utc),
            })

        OAuthAccountRepository.create({
            "user_id": user.id,
            "provider": "google",
            "provider_user_id": google_user_id,
        })

    tokens = generate_tokens(user_id=user.id, role=user.role)
    result = UserResponseSchema().dump(user)

    response, status_code = success_response(data=result, status_code=200)
    set_access_cookies(response, tokens["access_token"])
    return response, status_code


def _validate_verification_token(token: str):
    """Valida un token de verificación sin mutar ningún estado. Retorna (token_row, user, None) si el token es válido; retorna (None, None, response_tuple) con el error correspondiente si no lo es. Esta función es segura para llamarse desde un GET, no escribe en base de datos"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    token_row = EmailVerificationTokenRepository.get_by_token_hash(token_hash)

    if not token_row:
        return None, None, error_response(
            code="TOKEN_INVALID",
            message="El enlace de verificación no es válido.",
            status_code=404,
        )

    if token_row.used_at is not None:
        return None, None, error_response(
            code="TOKEN_ALREADY_USED",
            message="Este correo ya fue verificado anteriormente.",
            status_code=409,
        )

    now = datetime.now(timezone.utc)
    expires_aware = (
        token_row.expires_at.replace(tzinfo=timezone.utc)
        if token_row.expires_at.tzinfo is None
        else token_row.expires_at
    )
    if expires_aware < now:
        return None, None, error_response(
            code="TOKEN_EXPIRED",
            message="El enlace expiró. Solicita uno nuevo.",
            status_code=410,
        )

    user = UserRepository.get_by_id(token_row.user_id)
    return token_row, user, None


@auth_bp.route("/verify-email", methods=["GET"])
def verify_email_check():
    """GET solo valida el token, sin marcar nada como usado ni verificar la cuenta. Seguro para ser prefetcheado por escáneres de correo, no tiene efectos secundarios. Responde 200 con {valid: true, email} si el token sigue siendo válido"""
    token = request.args.get("token")
    if not token:
        return error_response(
            code="VALIDATION_ERROR",
            message="El token es obligatorio.",
            status_code=422,
        )

    token_row, user, err = _validate_verification_token(token)
    if err:
        return err

    return success_response(
        data={"valid": True, "email": user.email if user else None},
        status_code=200,
    )


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email_confirm():
    """POST ejecuta la verificación real tras la confirmación explícita del usuario. Vuelve a validar el token para cubrir la ventana entre el GET y el clic del usuario (race condition o token consumido en paralelo). Si sigue siendo válido, muta el estado: marca email_verified_at en el usuario y used_at en el token"""
    data = request.get_json() or {}
    token = data.get("token")
    if not token:
        return error_response(
            code="VALIDATION_ERROR",
            message="El token es obligatorio.",
            status_code=422,
        )

    token_row, user, err = _validate_verification_token(token)
    if err:
        return err

    now = datetime.now(timezone.utc)
    if user:
        user.email_verified_at = now
        UserRepository.save(user)

    EmailVerificationTokenRepository.mark_as_used(token_row)

    return success_response(
        data={"message": "Correo verificado correctamente."},
        status_code=200,
    )


@auth_bp.route("/resend-verification", methods=["POST"])
@limiter.limit("3 per hour")
def resend_verification():
    try:
        data = EmailOnlySchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)
        
    generic_ok, status_code = success_response(data={"message": "Si el correo existe y no ha sido verificado, se envió un nuevo enlace."}, status_code=200)
    
    user = UserRepository.get_by_email(data["email"])
    if not user or user.email_verified_at is not None:
        return generic_ok, status_code
        
    unused_tokens = EmailVerificationTokenRepository.get_unused_by_user_id(user.id)
    for t in unused_tokens:
        EmailVerificationTokenRepository.mark_as_used(t)
        
    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    from app.services.email_service import send_verification_email, build_verification_link
    try:
        EmailVerificationTokenRepository.create({
            "user_id": user.id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        })
        logger.info(f"[DEV] Verification link para {user.email}: {build_verification_link(plain_token)}")
        send_verification_email(user.email, plain_token)
    except AppError as e:
        logger.error(f"Error creando token de verificacion para {user.email}: {e.message}")
    except Exception as e:
        logger.error(f"Error reenviando correo de verificación a {user.email}: {str(e)}")

    return generic_ok, status_code




@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("3 per hour")
def forgot_password():
    try:
        data = ForgotPasswordSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    # Respuesta identica si el correo existe o no; evita que un atacante enumere qué correos están registrados en la plataforma.
    generic_ok = success_response(
        data={"message": "Si el correo existe, se enviará un enlace de recuperación."},
        status_code=200,
    )

    user = UserRepository.get_by_email(data["email"])
    if not user:
        return generic_ok

    # El token en texto plano solo vive en memoria durante esta request; guardamos su hash SHA-256 en la base de datos, nunca el valor original.
    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    from app.services.email_service import send_password_reset_email, EmailDeliveryError, build_password_reset_link
    try:
        PasswordResetTokenRepository.create({
            "user_id": user.id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        })
        reset_url = build_password_reset_link(plain_token)
        logger.info("[DEV] Reset link para %s: %s", user.email, reset_url)
        send_password_reset_email(user.email, plain_token)
    except EmailDeliveryError as e:
        logger.error(f"Error enviando correo de recuperación a {user.email}: {str(e)}")
    except AppError as e:
        logger.error(f"Error creando token de recuperacion para {user.email}: {e.message}")

    return generic_ok


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        data = ResetPasswordSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    token_hash = hashlib.sha256(data["token"].encode()).hexdigest()
    token_row = PasswordResetTokenRepository.get_by_token_hash(token_hash)

    now = datetime.now(timezone.utc)
    expires_aware = token_row.expires_at.replace(tzinfo=timezone.utc) if token_row and token_row.expires_at.tzinfo is None else (token_row.expires_at if token_row else None)

    if (
        not token_row
        or token_row.used_at is not None
        or (expires_aware and expires_aware < now)
    ):
        return error_response(
            code="INVALID_TOKEN",
            message="El enlace de recuperación no es válido o ya expiró.",
            status_code=400,
        )

    user = UserRepository.get_by_id(token_row.user_id)
    if not user:
        return error_response(
            code="NOT_FOUND",
            message="El usuario asociado a este token ya no existe.",
            status_code=404,
        )

    # Actualizamos el hash de la contraseña con el mismo mecanismo bcrypt que usa el registro normal, no se reinventa ningun mecanismo de cifrado. password_changed_at se actualiza en el mismo save() para invalidar todos los JWT emitidos antes de este momento; un atacante que hubiera robado un token activo queda bloqueado inmediatamente sin acción adicional.
    user.password_hash = hash_password(data["new_password"])
    user.password_changed_at = datetime.now(timezone.utc)
    UserRepository.save(user)

    # Invalidamos el token de inmediato para que no pueda reutilizarse.
    PasswordResetTokenRepository.mark_as_used(token_row)

    return success_response(data={"message": "Contraseña actualizada correctamente."}, status_code=200)
