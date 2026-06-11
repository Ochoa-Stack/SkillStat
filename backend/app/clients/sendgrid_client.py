from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app
from app.utils.errors import AppError

class EmailClient:
    # Envolvemos el SDK de SendGrid. Si en el futuro cambiamos a AWS SES o Mailgun,
    # los servicios del sistema no tendrán que ser modificados, limitando el impacto a esta clase.

    @classmethod
    def send_alert_email(cls, to_email: str, subject: str, html_content: str) -> bool:
        api_key = current_app.config.get("SENDGRID_API_KEY")
        from_email = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@skillstat.com")

        if not api_key:
            raise AppError("Clave de API de SendGrid no configurada en el entorno.", status_code=500)

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        try:
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            # SendGrid devuelve 202 (Accepted) cuando encola el correo correctamente para su envío
            return str(response.status_code).startswith("20")
        except Exception as e:
            raise AppError(f"Fallo de comunicación con el proveedor de correo: {str(e)}", code="EXTERNAL_API_ERROR")
