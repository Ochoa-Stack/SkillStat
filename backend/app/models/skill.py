from app.extensions import db


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    canonical_name = db.Column(db.String(100), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    # Relacionamos bidireccionalmente mediante el patrón Association Object para mantener la normalización 3FN en job_skills
    job_skills = db.relationship("JobSkill", backref="skill", lazy=True)
    alerts = db.relationship("Alert", backref="skill", lazy=True)
    trend_snapshots = db.relationship("TrendSnapshot", backref="skill", lazy=True)
