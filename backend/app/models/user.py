from app.extensions import db
from datetime import datetime, timezone


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    alerts = db.relationship("Alert", backref="user", lazy=True)
    backups = db.relationship("Backup", backref="user", lazy=True)

    # Restringimos los roles permitidos directamente en la base de datos por seguridad
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('GUEST', 'REGISTERED', 'ADMIN')", name="chk_users_role"
        ),
    )

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name} ({self.email})>"
