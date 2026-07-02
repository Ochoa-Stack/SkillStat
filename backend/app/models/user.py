from app.extensions import db
from datetime import datetime, timezone


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    # Nullable porque un usuario que entra solo via Google/GitHub/Apple nunca define una contrasena propia.
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Null para usuarios exclusivamente OAuth (sin contraseña propia). El blocklist callback trata null como "sin restricción"; esos usuarios nunca se desloguean por este mecanismo porque no tienen contraseña que cambiar.
    password_changed_at = db.Column(db.DateTime, nullable=True)
    # Null es el estado valido para "sin definir"; el valor se puede completar mas adelante desde el perfil.
    intent = db.Column(db.String(20), nullable=True)

    alerts = db.relationship("Alert", backref="user", lazy=True)
    backups = db.relationship("Backup", backref="user", lazy=True)
    oauth_accounts = db.relationship("OAuthAccount", backref="user", lazy=True)
    user_skills = db.relationship("UserSkill", backref="user", lazy=True)

    # Restringimos los roles y los intents permitidos directamente en la base de datos por seguridad
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('REGISTERED', 'ADMIN')", name="chk_users_role"
        ),
        db.CheckConstraint(
            "intent IS NULL OR intent IN ('ESTUDIANTE', 'RECLUTADOR')", name="chk_users_intent"
        ),
    )

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name} ({self.email})>"
