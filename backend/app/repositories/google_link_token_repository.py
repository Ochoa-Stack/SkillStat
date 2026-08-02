from datetime import datetime, timezone
from app.models.google_link_token import GoogleLinkToken
from app.repositories.base_repository import BaseRepository
from app.extensions import db

class GoogleLinkTokenRepository(BaseRepository):
    model = GoogleLinkToken

    @classmethod
    def get_by_token_hash(cls, token_hash: str):
        # Búsqueda principal del flujo de confirmación: localiza el token por su hash para validar vigencia y uso antes de completar la vinculación de cuenta.
        return db.session.execute(
            db.select(GoogleLinkToken).filter_by(token_hash=token_hash)
        ).scalar_one_or_none()

    @classmethod
    def mark_as_used(cls, token: GoogleLinkToken):
        # Invalida el token en el mismo instante en que se consume, impide que el mismo link de confirmación sirva para vincular dos veces.
        token.used_at = datetime.now(timezone.utc)
        return cls.save(token)
