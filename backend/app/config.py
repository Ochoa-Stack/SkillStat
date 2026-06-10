import os
from datetime import timedelta


class BaseConfig:
    """Configuración base compartida por todos los entornos"""

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
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 86400))
    )

    JWT_ERROR_MESSAGE_KEY = "error"

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5500").split(",")

    # APIs externas
    ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID")
    ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY")
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

    # Almacenamiento de respaldos
    BACKUP_STORAGE_URL = os.environ.get("BACKUP_STORAGE_URL")
    BACKUP_STORAGE_KEY = os.environ.get("BACKUP_STORAGE_KEY")

    # Scheduler
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "false").lower() == "true"
    INGESTION_INTERVAL_HOURS = int(os.environ.get("INGESTION_INTERVAL_HOURS", 6))
    TRENDS_INTERVAL_HOURS = int(os.environ.get("TRENDS_INTERVAL_HOURS", 24))


class DevelopmentConfig(BaseConfig):
    """Configuración para el entorno de desarrollo local"""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/skillstat_dev",
    )


class ProductionConfig(BaseConfig):
    """Configuración para el entorno de producción"""

    DEBUG = False
    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 10,
        "max_overflow": 20,
    }


class TestingConfig(BaseConfig):
    """Configuración para el entorno de pruebas automatizadas"""

    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)

    SCHEDULER_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
