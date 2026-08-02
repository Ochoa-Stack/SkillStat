import logging

from flask import Blueprint, request, current_app
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies
from marshmallow import ValidationError

from app.schemas.auth_schema import (
    UserRegistrationSchema,
    UserLoginSchema,
    UserResponseSchema,
    ForgotPasswordSchema,
    EmailOnlySchema,
    ResetPasswordSchema,
)
from app.services.auth_service import AuthService
from app.utils.response import success_response, error_response
from app.utils.errors import AppError, ConflictError
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

    try:
        user, plain_token = AuthService.register(data)
    except ConflictError:
        return error_response(code="CONFLICT", message="El correo ya está registrado.", status_code=409)

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

    try:
        user, tokens = AuthService.login(data)
    except AppError as err:
        return error_response(code=err.code, message=err.message, status_code=err.status_code)

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

@auth_bp.route("/google", methods=["POST"])
@limiter.limit("10 per 15 minutes")
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
        user, tokens = AuthService.authenticate_with_google(
            credential=credential,
            google_client_id=current_app.config["GOOGLE_CLIENT_ID"],
        )
    except AppError as err:
        if err.code == "ACCOUNT_LINK_PENDING":
            # El servicio detectó que ya existe una cuenta con ese email. Se devuelve 200 con ACCOUNT_LINK_PENDING y el link_token para que el frontend muestre la pantalla de confirmación antes de vincular. No se emite cookie de sesión todavía.
            return success_response(
                data={
                    "code": err.code,
                    "message": err.message,
                    **(err.detail or {}),
                },
                status_code=200,
            )
        return error_response(code=err.code, message=err.message, status_code=err.status_code)

    result = UserResponseSchema().dump(user)
    response, status_code = success_response(data=result, status_code=200)
    set_access_cookies(response, tokens["access_token"])
    return response, status_code


@auth_bp.route("/google/confirm-link", methods=["POST"])
@limiter.limit("10 per 15 minutes")
def google_confirm_link():
    """ Completa la vinculación de cuenta Google pendiente tras confirmación explícita del usuario. Recibe el link_token emitido por POST /google cuando se detectó una cuenta existente con el mismo email. Si el token es válido, crea el OAuthAccount, lo marca como usado, y emite la cookie de sesión. """
    data = request.get_json() or {}
    link_token = data.get("link_token")

    if not link_token:
        return error_response(
            code="VALIDATION_ERROR",
            message="El link_token es obligatorio.",
            status_code=422,
        )

    try:
        user, tokens = AuthService.confirm_google_link(link_token)
    except AppError as err:
        return error_response(code=err.code, message=err.message, status_code=err.status_code)

    result = UserResponseSchema().dump(user)
    response, status_code = success_response(data=result, status_code=200)
    set_access_cookies(response, tokens["access_token"])
    return response, status_code


@auth_bp.route("/verify-email", methods=["GET"])
def verify_email_check():
    """GET solo valida el token, sin marcar nada como usado ni verificar la cuenta. Seguro para ser prefetcheado por escáneres de correo, no tiene efectos secundarios. Responde 200 con {valid: true, email} si el token sigue siendo válido. """
    token = request.args.get("token")
    if not token:
        return error_response(
            code="VALIDATION_ERROR",
            message="El token es obligatorio.",
            status_code=422,
        )

    try:
        result = AuthService.verify_email_check(token)
    except AppError as err:
        return error_response(code=err.code, message=err.message, status_code=err.status_code)

    return success_response(data=result, status_code=200)

@auth_bp.route("/verify-email", methods=["POST"])
def verify_email_confirm():
    """POST ejecuta la verificación real tras la confirmación explícita del usuario. Vuelve a validar el token para cubrir la ventana entre el GET y el clic del usuario (race condition o token consumido en paralelo). Si sigue siendo válido, muta el estado: marca email_verified_at en el usuario y used_at en el token. """
    data = request.get_json() or {}
    token = data.get("token")
    if not token:
        return error_response(
            code="VALIDATION_ERROR",
            message="El token es obligatorio.",
            status_code=422,
        )

    try:
        AuthService.verify_email_confirm(token)
    except AppError as err:
        return error_response(code=err.code, message=err.message, status_code=err.status_code)

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

    try:
        plain_token, user_email = AuthService.resend_verification(data["email"])
    except AppError as e:
        logger.error(f"Error creando token de verificacion: {e.message}")
        return generic_ok, status_code

    if plain_token is None:
        return generic_ok, status_code

    from app.services.email_service import send_verification_email, build_verification_link
    try:
        logger.info(f"[DEV] Verification link para {user_email}: {build_verification_link(plain_token)}")
        send_verification_email(user_email, plain_token)
    except Exception as e:
        logger.error(f"Error reenviando correo de verificación a {user_email}: {str(e)}")

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

    try:
        plain_token, user_email = AuthService.forgot_password(data["email"])
    except AppError as e:
        logger.error(f"Error creando token de recuperacion: {e.message}")
        return generic_ok

    if plain_token is None:
        return generic_ok

    from app.services.email_service import send_password_reset_email, EmailDeliveryError, build_password_reset_link
    try:
        reset_url = build_password_reset_link(plain_token)
        logger.info("[DEV] Reset link para %s: %s", user_email, reset_url)
        send_password_reset_email(user_email, plain_token)
    except EmailDeliveryError as e:
        logger.error(f"Error enviando correo de recuperación a {user_email}: {str(e)}")

    return generic_ok

@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("3 per hour")
def reset_password():
    try:
        data = ResetPasswordSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response(code="VALIDATION_ERROR", message=err.messages, status_code=422)

    try:
        AuthService.reset_password(data["token"], data["new_password"])
    except AppError as err:
        return error_response(code=err.code, message=err.message, status_code=err.status_code)

    return success_response(data={"message": "Contraseña actualizada correctamente."}, status_code=200)
