import resend
from flask import current_app
import logging
from app.utils.errors import AppError

logger = logging.getLogger(__name__)

class EmailDeliveryError(AppError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, code="EMAIL_DELIVERY_ERROR", status_code=status_code)


def build_verification_link(token: str) -> str:
    """Construye el enlace de verificación de correo a partir del token en texto plano.
    Punto único de verdad para la URL; cualquier cambio de ruta o dominio se hace aquí"""
    return f"{current_app.config['FRONTEND_BASE_URL']}/views/verificar-correo.html?token={token}"


def send_verification_email(to_email: str, token: str) -> None:
    resend.api_key = current_app.config["RESEND_API_KEY"]
    from_email = current_app.config.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    verification_link = build_verification_link(token)
    
    html_content = f"""
    <p>Hola,</p>
    <p>Por favor verifica tu correo electrónico haciendo clic en el siguiente enlace:</p>
    <p><a href="{verification_link}">{verification_link}</a></p>
    """
    
    try:
        response = resend.Emails.send({
            "from": from_email,
            "to": to_email,
            "subject": "Verifica tu correo en SkillStat",
            "html": html_content
        })
        logger.info(f"Correo de verificación enviado a {to_email}. ID: {response.get('id')}")
        return response
    except Exception as e:
        logger.error(f"Error al enviar correo de verificación a {to_email}: {str(e)}")
        raise EmailDeliveryError(f"No se pudo enviar el correo de verificación: {str(e)}")
