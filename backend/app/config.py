import os
from datetime import timedelta


class BaseConfig:

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-in-production")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY", "jwt-insecure-key-change-in-production"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 7200))
    )
    JWT_ERROR_MESSAGE_KEY = "error"
    # El JWT vive en una cookie httpOnly en vez de viajar en el cuerpo JSON, para que un script de XSS no pueda leerlo directamente.
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_BLOCKLIST_TOKEN_CHECKS = ["access", "refresh"]
    JWT_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "false").lower() == "true"
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = True

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5500").split(",")
    FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5500/frontend")

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID")
    ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY")
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    
    # Validación explícita en arranque (guard incondicional)
    if not RESEND_API_KEY:
        raise ValueError("Error de arranque: RESEND_API_KEY es obligatoria y no está configurada en el entorno.")

    R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
    R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
    R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")

    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "false").lower() == "true"
    INGESTION_INTERVAL_HOURS = int(os.environ.get("INGESTION_INTERVAL_HOURS", 6))
    TRENDS_INTERVAL_HOURS = int(os.environ.get("TRENDS_INTERVAL_HOURS", 24))

    # Clave secreta para el endpoint POST /api/admin/trigger-pipeline, que es invocado por GitHub Actions sin sesión de usuario. Se valida via el header X-Pipeline-Trigger-Key usando comparación de tiempo constante (hmac.compare_digest).
    PIPELINE_TRIGGER_SECRET = os.environ.get("PIPELINE_TRIGGER_SECRET")

    # Validación explícita en arranque (guard incondicional)
    if not PIPELINE_TRIGGER_SECRET:
        raise ValueError(
            "Error de arranque: PIPELINE_TRIGGER_SECRET es obligatoria y no está configurada en el entorno."
        )



class DevelopmentConfig(BaseConfig):

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/skillstat_dev",
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "connect_args": {
            "client_encoding": "utf8",
            "options": "-c lc_messages=C",
        },
    }


class ProductionConfig(BaseConfig):

    DEBUG = False
    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 10,
        "max_overflow": 20,
    }


class TestingConfig(BaseConfig):

    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:Ochoa-Stack@localhost:5432/skillstat_test",
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "connect_args": {
            "client_encoding": "utf8",
            "options": "-c lc_messages=C",
        },
    }

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)

    SCHEDULER_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
