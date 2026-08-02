from datetime import datetime, timezone
from app.extensions import db

class GoogleLinkToken(db.Model):
    """ Token de corta vida que transporta la identidad de Google entre el primer intento de login (POST /google) y la confirmación explícita del usuario (POST /google/confirm-link). Solo se genera cuando existe ya un User con el mismo email pero sin OAuthAccount vinculado; el caso de cuenta nueva no pasa por este flujo. """

    __tablename__ = "google_link_tokens"

    id = db.Column(db.Integer, primary_key=True)
    # El usuario cuya cuenta se va a vincular si el token se confirma.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Hash SHA-256 del token en texto plano. El token plano NUNCA se persiste, solo existe en la respuesta JSON que el controlador devuelve al frontend para que lo reenvíe en la confirmación.
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    # Identidad de Google que se vinculará al confirmar; necesaria para crear el OAuthAccount sin volver a verificar el token de Google.
    google_user_id = db.Column(db.String(255), nullable=False)
    # Datos del perfil de Google que se usarán si se actualiza el perfil del usuario tras la vinculación (fuera de alcance en esta ronda, pero presentes en la tabla para no requerir una migración adicional después).
    pending_email = db.Column(db.String(254), nullable=False)
    pending_first_name = db.Column(db.String(100), nullable=True)
    pending_last_name = db.Column(db.String(100), nullable=True)
    # Ventana de confirmación: 15 minutos es suficiente para que el usuario lea la pantalla de confirmación y haga clic, sin ser tan larga como para acumular tokens no confirmados indefinidamente.
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.Index("ix_google_link_tokens_token_hash", "token_hash"),
    )

    def __repr__(self):
        return f"<GoogleLinkToken user_id={self.user_id} google_user_id={self.google_user_id} expires_at={self.expires_at}>"
