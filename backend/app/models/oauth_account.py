from datetime import datetime, timezone
from app.extensions import db


class OAuthAccount(db.Model):
    __tablename__ = "oauth_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    provider = db.Column(db.String(20), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Restringimos a los proveedores que el equipo planea soportar, igual que el CHECK de role en User, para que agregar GitHub o Apple despues solo amplie esta lista, sin rediseñar la tabla.
    __table_args__ = (
        db.CheckConstraint(
            "provider IN ('google', 'github', 'apple')",
            name="chk_oauth_accounts_provider",
        ),
        db.UniqueConstraint(
            "provider", "provider_user_id", name="uq_oauth_accounts_provider_identity"
        ),
    )

    def __repr__(self):
        return f"<OAuthAccount {self.provider}:{self.provider_user_id} -> user_id={self.user_id}>"
