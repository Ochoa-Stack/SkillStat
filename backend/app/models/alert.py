from app.extensions import db
from datetime import datetime, timezone


class Alert(db.Model):
    __tablename__ = "user_alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False, default="ABSOLUTE")
    # Nullable porque solo aplica a alertas de tipo ABSOLUTE
    threshold_value = db.Column(db.Integer, nullable=True)
    # Nullable porque solo aplica a alertas de tipo TREND
    threshold_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.CheckConstraint(
            "alert_type IN ('ABSOLUTE', 'TREND')", name="chk_alerts_type"
        ),
        db.CheckConstraint(
            "(alert_type = 'ABSOLUTE' AND threshold_value IS NOT NULL) OR "
            "(alert_type = 'TREND' AND threshold_percentage IS NOT NULL)",
            name="chk_alerts_threshold_matches_type",
        ),
    )
