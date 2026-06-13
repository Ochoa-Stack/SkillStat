import os
from flask import Flask
from dotenv import load_dotenv

from app.config import config_map
from app.extensions import db, jwt, cors, migrate, scheduler

def create_app(env: str = None) -> Flask:
    # Patrón Application Factory. Aísla la inicialización para permitir múltiples instancias durante pruebas automatizadas y evita variables globales.
    load_dotenv()
    
    app = Flask(__name__)
    
    env = env or os.environ.get("FLASK_ENV", "development")
    config_class = config_map.get(env, config_map["development"])
    app.config.from_object(config_class)

    _init_extensions(app)
    _register_blueprints(app)
    _register_schedulers(app)

    return app

def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    # Habilitamos CORS estrictamente para la ruta de la API para permitir el consumo desde el Single Page Application de React en el Frontend.
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

def _register_blueprints(app: Flask) -> None:
    # Importaciones diferidas para prevenir dependencias circulares antes de inicializar Flask
    from app.controllers.auth_bp import auth_bp
    from app.controllers.panorama_bp import panorama_bp
    from app.controllers.alerts_bp import alerts_bp
    from app.controllers.admin_bp import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(panorama_bp, url_prefix="/api/panorama")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

def _register_schedulers(app: Flask) -> None:
    # Programación de tareas en segundo plano. Cumple con el requisito de automatización.
    from app.services.market_trends_service import MarketTrendsService
    from app.services.alerts_service import AlertsService

    def daily_pipeline():
        with app.app_context():
            MarketTrendsService.generate_snapshots()
            AlertsService.evaluate_and_notify()

    # Si el scheduler no está corriendo, lo iniciamos y programamos el pipeline
    if not scheduler.running:
        scheduler.add_job(func=daily_pipeline, trigger="cron", hour=0, minute=0, id="daily_pipeline", replace_existing=True)
        scheduler.start()
