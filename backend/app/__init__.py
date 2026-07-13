import os
import logging_config
from flask import Flask

from app.config import config_map
from app.extensions import db, jwt, cors, migrate, scheduler

def create_app(env: str = None) -> Flask:
    # Aplicamos el patrón Application Factory porque aislar la inicialización nos permite instanciar aplicaciones independientes durante las pruebas automatizadas, previniendo choques por estado global.
    
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

    @jwt.revoked_token_loader
    def handle_revoked_token(jwt_header, jwt_payload):
        return error_response(
            code="TOKEN_REVOKED",
            message="La sesión ha sido revocada.",
            status_code=401,
        )

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        # Importación diferida para evitar ciclo de importación con db/User.
        from app.repositories.user_repository import UserRepository
        from datetime import datetime, timezone as tz

        user_id = jwt_payload.get("sub")
        if not user_id:
            return False

        user = UserRepository.get_by_id(int(user_id))
        if not user:
            # Si Usuario no encontrado, entonces no podemos validar nada, dejamos pasar (flask-jwt-extended ya maneja tokens huérfanos en otros callbacks).
            return False

        if not user.is_active:
            # Si Usuario desactivado, entonces revocamos inmediatamente todas sus sesiones activas sin importar cuándo fue emitido el token.
            return True

        if user.password_changed_at is None:
            # Si Usuario exclusivamente OAuth (sin contraseña propia), no aplicamos invalidación por cambio de contraseña.
            return False

        # El claim "iat" (issued-at) es un timestamp Unix con precisión de segundos. password_changed_at tiene microsegundos; truncamos al segundo para que un token emitido en el mismo segundo que el reset no quede bloqueado falsamente. El ataque de "token emitido justo antes del reset" sigue bloqueado correctamente porque iat < pca_floor cuando la diferencia es de al menos 1 segundo completo.
        iat = jwt_payload.get("iat", 0)
        pca = user.password_changed_at
        if pca.tzinfo is None:
            pca = pca.replace(tzinfo=tz.utc)

        # Truncamos la marca de tiempo de cambio de contraseña a segundos exactos porque el claim 'iat' del JWT no tiene milisegundos; esto previene que revoquemos accidentalmente un token legítimo emitido durante el mismo segundo del cambio.
        pca_floor = pca.replace(microsecond=0)

        token_issued_at = datetime.fromtimestamp(iat, tz=tz.utc)
        return token_issued_at < pca_floor


def _register_blueprints(app: Flask) -> None:
    # Importaciones diferidas para prevenir dependencias circulares antes de inicializar Flask
    from app.controllers.auth_bp import auth_bp
    from app.controllers.panorama_bp import panorama_bp
    from app.controllers.alerts_bp import alerts_bp
    from app.controllers.admin_bp import admin_bp
    from app.controllers.profile_bp import profile_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(panorama_bp, url_prefix="/api/panorama")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")

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
