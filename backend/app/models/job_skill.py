from app.extensions import db
from datetime import datetime, timezone


class JobSkill(db.Model):
    __tablename__ = "job_skills"

    # Utilizamos llave primaria compuesta para evitar identificadores subrogados innecesarios y cumplir la 3FN
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), primary_key=True)

    confidence_score = db.Column(db.Numeric(4, 3), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
