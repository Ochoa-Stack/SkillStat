from app.extensions import db
from datetime import datetime, timezone


class UserSkill(db.Model):
    __tablename__ = "user_skills"

    # Utilizamos llave primaria compuesta para evitar identificadores subrogados innecesarios y cumplir la tercera forma normal, siguiendo el mismo patron que ya implementamos en job_skills.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), primary_key=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
