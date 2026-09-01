from app.extensions import db
from datetime import datetime, timezone


class Backup(db.Model):
    __tablename__ = "backups"

    id = db.Column(db.Integer, primary_key=True)
    # Habilitamos nulos para soportar la ejecución de respaldos automáticos desde el scheduler sin un usuario físico atado
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    storage_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False)
    file_size_bytes = db.Column(db.BigInteger, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'FAILED')", name="chk_backups_status"
        ),
    )
