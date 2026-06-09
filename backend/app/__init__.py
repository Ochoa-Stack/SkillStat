# Construimos la aplicación usando el patrón application factory para poder
# crear instancias independientes según el entorno: desarrollo, producción o pruebas
import os
from flask import Flask, jsonify
from dotenv import load_dotenv

from app.config import config_map
from app.extensions import db, jwt, cors, migrate


def create_app(env: str = None) -> Flask:
    """Crea y configura una instancia de la aplicación Flask"""

    # Cargamos las variables de entorno antes de leer cualquier configuración para que estén disponibles cuando se instancian las clases de config
    load_dotenv()

    app = Flask(__name__, instance_relative_config=False)

    # Seleccionamos la configuración según el entorno
    env = env or os.environ.get("FLASK_ENV", "development")
    config_class = config_map.get(env, config_map["development"])
    app.config.from_object(config_class)

    # Verificamos que la base de datos esté configurada antes de continuar
    # Hacemos esta validación aquí y no en la clase de configuración para que ocurra en tiempo de ejecución real y solo cuando el entorno es producción
    if env == "production" and not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError(
            "DATABASE_URL no está definida. "
            "La aplicación no puede iniciar en producción sin una base de datos configurada."
        )

    _init_extensions(app)

    # Importamos los modelos para que SQLAlchemy registre sus tablas en el metadata antes de que Alembic las lea durante la generación de migraciones
    from app import models as _models  # noqa: F401

    _register_blueprints(app)
    _register_error_handlers(app)
    _register_health_check(app)

    return app


def _init_extensions(app: Flask) -> None:
    """Conecta las extensiones con la instancia de la aplicación"""
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
    )
    migrate.init_app(app, db)
    _configure_jwt_errors()


def _configure_jwt_errors() -> None:
    """Registra los manejadores de error de JWT para que sigan el formato
    uniforme de la API en lugar del formato por defecto de la librería"""

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return jsonify({
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "El token de acceso ha expirado. Inicia sesión de nuevo.",
            }
        }), 401

    @jwt.invalid_token_loader
    def invalid_token(_error):
        return jsonify({
            "error": {
                "code": "TOKEN_INVALID",
                "message": "El token de acceso no es válido.",
            }
        }), 401

    @jwt.unauthorized_loader
    def missing_token(_error):
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Se requiere un token de acceso para usar este recurso.",
            }
        }), 401


def _register_blueprints(app: Flask) -> None:
    """Registra los Blueprints con sus prefijos de ruta correspondientes.
    Importamos dentro de la función para evitar importaciones circulares
    durante la inicialización de las extensiones"""
    from app.controllers.auth_bp import auth_bp
    from app.controllers.panorama_bp import panorama_bp
    from app.controllers.alerts_bp import alerts_bp
    from app.controllers.admin_bp import admin_bp

    app.register_blueprint(auth_bp,     url_prefix="/api/auth")
    app.register_blueprint(panorama_bp, url_prefix="/api/panorama")
    app.register_blueprint(alerts_bp,   url_prefix="/api/alerts")
    app.register_blueprint(admin_bp,    url_prefix="/api/admin")


def _register_error_handlers(app: Flask) -> None:
    """Registra los manejadores de error HTTP para devolver respuestas JSON
    con el formato uniforme de la API en lugar de páginas HTML por defecto"""

    @app.errorhandler(400)
    def bad_request(_error):
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "La solicitud no tiene el formato correcto.",
            }
        }), 400

    @app.errorhandler(401)
    def unauthorized(_error):
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Se requiere autenticación para acceder a este recurso.",
            }
        }), 401

    @app.errorhandler(403)
    def forbidden(_error):
        return jsonify({
            "error": {
                "code": "FORBIDDEN",
                "message": "No tienes permiso para realizar esta acción.",
            }
        }), 403

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "El recurso solicitado no existe.",
            }
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "El método HTTP no está permitido para este recurso.",
            }
        }), 405

    @app.errorhandler(409)
    def conflict(_error):
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": "El recurso ya existe o hay un conflicto con el estado actual.",
            }
        }), 409

    @app.errorhandler(422)
    def unprocessable_entity(_error):
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Los datos enviados no pasaron la validación.",
            }
        }), 422

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Ocurrió un error interno. Por favor intenta de nuevo.",
            }
        }), 500


def _register_health_check(app: Flask) -> None:
    """Registra el endpoint de salud para verificar que el servicio está activo"""

    @app.route("/api/health")
    def health_check():
        return jsonify({
            "status": "ok",
            "service": "SkillStat API",
        }), 200