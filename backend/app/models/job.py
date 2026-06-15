from app.extensions import db
from datetime import datetime, timezone


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=True)
    # Permitimos nulos en city_id para no bloquear la ingesta de vacantes remotas o sin geolocalización
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=True)
    salary_min = db.Column(db.Numeric(10, 2), nullable=True)
    salary_max = db.Column(db.Numeric(10, 2), nullable=True)
    raw_description = db.Column(db.Text, nullable=False)

    # Guardamos el hash de la descripción para detectar rápidamente si una vacante ya fue procesada o si cambió en su origen
    description_hash = db.Column(db.String(64), nullable=False, unique=True)
    processed = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    job_skills = db.relationship("JobSkill", backref="job", lazy=True)
