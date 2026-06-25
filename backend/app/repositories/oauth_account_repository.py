from app.repositories.base_repository import BaseRepository
from app.models.oauth_account import OAuthAccount
from app.extensions import db


class OAuthAccountRepository(BaseRepository):
    model = OAuthAccount

    @classmethod
    def get_by_provider_identity(cls, provider: str, provider_user_id: str):
        # Busqueda especializada para el flujo de login: identifica si esta combinacion de proveedor + id externo ya esta vinculada a una cuenta existente.
        return db.session.execute(
            db.select(OAuthAccount).filter_by(
                provider=provider, provider_user_id=provider_user_id
            )
        ).scalar_one_or_none()
