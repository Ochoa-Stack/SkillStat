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
    _register_jwt_handlers(app)
    _register_blueprints(app)
    _register_schedulers(app)

    return app

def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    # Restringimos CORS al prefijo de la API para que el frontend pueda consumirla desde su propio origen sin bloqueos del navegador.
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*"), "supports_credentials": True}})

def _register_jwt_handlers(app: Flask) -> None:
    # Unificamos el formato de los errores que flask-jwt-extended genera directamente (antes de llegar a nuestras rutas) con el mismo formato {"error": {"code", "message"}} que usa el resto de la API.
    from app.utils.response import error_response

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return error_response(
            code="UNAUTHORIZED",
            message="No se encontró una sesión activa.",
            status_code=401,
        )

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return error_response(
            code="TOKEN_INVALID",
            message="La sesión no es válida.",
            status_code=401,
        )

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return error_response(
            code="TOKEN_EXPIRED",
            message="La sesión ha expirado, vuelve a iniciar sesión.",
            status_code=401,
        )


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
    from scheduler.jobs import daily_pipeline
    import functools

    # Vinculamos la instancia concreta de app al job para que APScheduler pueda ejecutarlo en su hilo sin depender del proxy.
    bound_pipeline = functools.partial(daily_pipeline, app)

    if not scheduler.running:
        scheduler.add_job(
            func=bound_pipeline,
            trigger="cron",
            hour=0,
            minute=0,
            id="daily_pipeline",
            replace_existing=True,
        )
        scheduler.start()
