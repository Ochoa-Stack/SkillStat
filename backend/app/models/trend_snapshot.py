from app.extensions import db

class TrendSnapshot(db.Model):
    __tablename__ = 'trend_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    demand_count = db.Column(db.Integer, default=0, nullable=True)
    growth_rate = db.Column(db.Numeric(6, 2), nullable=True)
    avg_salary = db.Column(db.Numeric(10, 2), nullable=True)

    # Forzamos unicidad combinada para garantizar que no existan métricas duplicadas para la misma ciudad, habilidad y fecha
    __table_args__ = (
        db.UniqueConstraint('skill_id', 'city_id', 'date', name='uq_trend_snapshot_skill_city_date'),
    )