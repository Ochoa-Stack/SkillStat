from app.extensions import db
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    alerts = db.relationship('Alert', backref='user', lazy=True)
    backups = db.relationship('Backup', backref='user', lazy=True)

    # Restringimos los roles permitidos directamente en la base de datos por seguridad
    __table_args__ = (
        db.CheckConstraint("role IN ('GUEST', 'REGISTERED', 'ADMIN')", name='chk_users_role'),
    )