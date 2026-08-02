import os
from urllib.parse import urlparse
from sqlalchemy import text
from flask_migrate import upgrade
import subprocess
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.repositories.backup_repository import BackupRepository
from app.utils.errors import AppError
from app.services.storage_service import RemoteStorageService
import logging

logger = logging.getLogger(__name__)

class BackupService:
    # Encapsula la ejecución de comandos del sistema operativo (pg_dump). Requisito obligatorio de infraestructura y recuperación.

    @classmethod
    def _get_connection_params(cls, db_url: str) -> dict:
        # Usamos urlparse para manejar correctamente passwords con caracteres especiales que el split manual no puede resolver.
        parsed = urlparse(db_url)
        password = parsed.password or ""
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        return {
            "host": parsed.hostname,
            "port": str(parsed.port or 5432),
            "user": parsed.username,
            "db_name": parsed.path.lstrip("/"),
            "env": env,
        }

    @classmethod
    def execute_database_backup(cls, requested_by: int = None) -> dict:

        db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")

        if not db_url or "postgresql" not in db_url:
            raise AppError(
                "El servicio de respaldo solo soporta motores PostgreSQL nativos.",
                status_code=500,
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"skillstat_backup_{timestamp}.sql"

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        backup_dir = os.path.join(base_dir, "data", "backups")
        os.makedirs(backup_dir, exist_ok=True)

        filepath = os.path.join(backup_dir, filename)

        backup_record = BackupRepository.create({
            "filename": filename,
            "storage_url": filepath,
            "status": "PENDING",
            "user_id": requested_by,
        })

        try:
            conn = cls._get_connection_params(db_url)

            command = [
                "pg_dump",
                "-h", conn["host"],
                "-p", conn["port"],
                "-U", conn["user"],
                "-F", "c",
                "-f", filepath,
                conn["db_name"],
            ]

            subprocess.run(command, env=conn["env"], capture_output=True, text=True, check=True)

            file_size = os.path.getsize(filepath)
            RemoteStorageService.upload_backup(filepath, filename)
            BackupRepository.update(
                backup_record.id,
                {"status": "COMPLETED", "file_size_bytes": file_size},
            )

            return {"status": "success", "file": filename, "size": file_size}

        except subprocess.CalledProcessError as e:
            try:
                BackupRepository.update(backup_record.id, {"status": "FAILED"})
            except AppError as update_err:
                logger.error(
                    "No se pudo marcar el backup %s como FAILED tras error de pg_dump: %s",
                    backup_record.id, update_err.message
                )
            raise AppError(
                f"Fallo en ejecucion de pg_dump: {e.stderr}",
                code="BACKUP_ERROR",
            )
        except Exception as e:
            try:
                BackupRepository.update(backup_record.id, {"status": "FAILED"})
            except AppError as update_err:
                logger.error(
                    "No se pudo marcar el backup %s como FAILED tras error interno: %s",
                    backup_record.id, update_err.message
                )
            raise AppError(
                f"Error interno durante respaldo: {str(e)}",
                code="BACKUP_ERROR",
            )

    @classmethod
    def restore_database_backup(cls, backup_id: int, requested_by: int) -> dict:
        backup = BackupRepository.get_by_id(backup_id)
        if not backup:
            raise AppError("El respaldo solicitado no existe.", code="NOT_FOUND", status_code=404)
        if backup.status != "COMPLETED":
            raise AppError(
                "Solo se pueden restaurar respaldos con estado COMPLETED.",
                code="INVALID_BACKUP_STATE",
                status_code=422,
            )
        if not os.path.exists(backup.storage_url):
            logger.warning(
                "Archivo de respaldo %s no encontrado localmente, intentando descargar desde R2.",
                backup.filename,
            )
            # Aseguramos que el directorio destino exista antes de escribir el archivo descargado (en un entorno recien desplegado podria no existir todavia).
            os.makedirs(os.path.dirname(backup.storage_url), exist_ok=True)
            downloaded = RemoteStorageService.download_backup(
                backup.filename, backup.storage_url
            )
            if not downloaded:
                raise AppError(
                    "El archivo de respaldo no existe localmente y no se pudo "
                    "descargar desde el almacenamiento remoto.",
                    code="BACKUP_FILE_MISSING",
                    status_code=404,
                )

        # Extraemos TODOS los valores primitivos que necesitamos del objeto backup ANTES de generar el backup de seguridad. Esto es critico porque cualquier acceso a un atributo del ORM despues del commit de execute_database_backup() dispara un lazy-load que abre una transaccion implicita nueva, la cual retiene un lock compartido sobre la tabla backups y causa un deadlock real con pg_restore, que necesita un lock exclusivo sobre esa misma tabla para hacer DROP CONSTRAINT/DROP TABLE. Confirmado con evidencia de pg_stat_activity durante el diagnostico de esta rama.
        backup_filepath = backup.storage_url
        backup_filename = backup.filename

        # Generamos el respaldo de seguridad ANTES de tocar la base de datos. Si esto falla, abortamos toda la operacion.
        safety_backup = cls.execute_database_backup(requested_by=requested_by)

        # Verificacion de defensa en profundidad, confirmamos que el archivo a restaurar sigue siendo distinto al respaldo de seguridad recien generado.
        if safety_backup["file"] == backup_filename:
            raise AppError(
                "Colision de nombre de archivo detectada entre el respaldo "
                "a restaurar y el respaldo de seguridad. Restauracion abortada "
                "por seguridad.",
                code="FILENAME_COLLISION",
                status_code=500,
            )

        db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        conn = cls._get_connection_params(db_url)

        # Cerramos explicitamente la sesion de SQLAlchemy ANTES del reset DDL y de pg_restore. Esto libera cualquier lock que la sesion actual pudiera estar reteniendo sobre las tablas (ej: locks por lazy-loading o transacciones de prueba abiertas) previniendo deadlocks durante el DROP SCHEMA y la recreación.
        db.session.remove()

        # Reseteamos el schema public completo antes de restaurar. El enfoque anterior solo emite DROPs para los objetos que están presentes en el dump, lo que causa un error cuando la BD actual tiene tablas con FK hacia objetos del dump que pg_restore intenta recrear (ej: google_link_tokens -> users). El DROP SCHEMA CASCADE elimina todo el grafo de objetos del schema, incluidas las FKs de tablas que el dump no conoce, dejando la BD estéril antes de la restauración. Las extensiones como unaccent se recuperan automáticamente: si el dump las incluye, pg_restore las recrea; si no, la llamada a upgrade() posterior vuelve a aplicar la migración correspondiente que las instala.
        with db.engine.execution_options(isolation_level="AUTOCOMMIT").connect() as raw_conn:
            raw_conn.execute(text("DROP SCHEMA public CASCADE"))
            raw_conn.execute(text("CREATE SCHEMA public"))
            raw_conn.execute(text("GRANT ALL ON SCHEMA public TO CURRENT_USER"))

        command = [
            "pg_restore",
            "-h", conn["host"],
            "-p", conn["port"],
            "-U", conn["user"],
            "-d", conn["db_name"],
            backup_filepath,
        ]

        try:
            subprocess.run(command, env=conn["env"], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise AppError(
                f"Fallo en ejecucion de pg_restore: {e.stderr}",
                code="RESTORE_ERROR",
                status_code=500,
            )

        # upgrade() usa la configuracion de directorio de migraciones registrada via migrate.init_app(app, db) en _init_extensions(), que apunta a backend/migrations/ (ubicacion default de flask_migrate, sin parametro directory adicional). Se invoca en un bloque separado para distinguir claramente un fallo de esquema de un fallo del propio pg_restore.
        try:
            upgrade()
        except Exception as e:
            logger.error(
                "Los datos se restauraron correctamente desde %s, pero la "
                "sincronizacion automatica del esquema (flask db upgrade) "
                "fallo: %s. Se requiere intervencion manual inmediata "
                "ejecutando 'flask db upgrade' desde la terminal.",
                backup_filename, str(e),
            )
            raise AppError(
                "El respaldo se restauro correctamente, pero la sincronizacion "
                "automatica del esquema de base de datos fallo. Los datos son "
                "validos pero el esquema puede estar desincronizado respecto "
                "al codigo actual. Ejecute 'flask db upgrade' manualmente de "
                "inmediato.",
                code="RESTORE_SCHEMA_SYNC_FAILED",
                status_code=500,
            )

        return {
            "status": "success",
            "restored_from": backup_filename,
            "safety_backup": safety_backup["file"],
        }
