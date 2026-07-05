from datetime import datetime, timezone
from app.models.email_verification_token import EmailVerificationToken
from app.repositories.base_repository import BaseRepository
from app.extensions import db

class EmailVerificationTokenRepository(BaseRepository):
    model = EmailVerificationToken

    @classmethod
    def get_by_token_hash(cls, token_hash: str) -> EmailVerificationToken:
        return cls.model.query.filter_by(token_hash=token_hash).first()

    @classmethod
    def mark_as_used(cls, token_instance: EmailVerificationToken) -> EmailVerificationToken:
        token_instance.used_at = datetime.now(timezone.utc)
        return cls.save(token_instance)

    @classmethod
    def get_unused_by_user_id(cls, user_id: int):
        return cls.model.query.filter_by(user_id=user_id, used_at=None).all()
