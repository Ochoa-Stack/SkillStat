from datetime import datetime, timezone
from app.repositories.base_repository import BaseRepository
from app.models.password_reset_token import PasswordResetToken
from app.extensions import db


class PasswordResetTokenRepository(BaseRepository):
    model = PasswordResetToken

    @classmethod
    def get_by_token_hash(cls, token_hash: str):
        # Búsqueda principal del flujo de reset, localiza el token por su hash para poder validar vigencia y uso antes de permitir el cambio de contraseña.
        return db.session.execute(
            db.select(PasswordResetToken).filter_by(token_hash=token_hash)
        ).scalar_one_or_none()

    @classmethod
    def mark_as_used(cls, token: PasswordResetToken):
        # Invalida el token en el mismo instante en que se consume, impide que un mismo link de reset sirva para cambiar la contraseña dos veces.
        token.used_at = datetime.now(timezone.utc)
        return cls.save(token)
