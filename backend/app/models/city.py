from app.extensions import db


class City(db.Model):
    __tablename__ = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    state = db.Column(db.String(100), nullable=True)
    # Establecemos México como default tanto a nivel aplicación como base de datos
    country = db.Column(db.String(10), default="MX", server_default="MX", nullable=True)
    lat = db.Column(db.Numeric(9, 6), nullable=True)
    lon = db.Column(db.Numeric(9, 6), nullable=True)

    jobs = db.relationship("Job", backref="city", lazy=True)
    trend_snapshots = db.relationship("TrendSnapshot", backref="city", lazy=True)
