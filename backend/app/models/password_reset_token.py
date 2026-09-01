from datetime import datetime, timezone
from app.extensions import db


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    # Si el usuario se elimina, sus tokens de reset se eliminan con el (ondelete CASCADE).
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Almacenamos el hash SHA-256 del token en texto plano. El token plano NUNCA se persiste, solo existe en el log de desarrollo y en el correo que el usuario recibe.
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    # used_at queda null mientras el token no se ha consumido.
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.Index("ix_password_reset_tokens_token_hash", "token_hash"),
    )

    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id} expires_at={self.expires_at}>"
