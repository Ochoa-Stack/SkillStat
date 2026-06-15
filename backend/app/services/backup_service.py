import os
import subprocess
from datetime import datetime
from flask import current_app
from app.repositories.backup_repository import BackupRepository
from app.utils.errors import AppError

class BackupService:
    # Encapsula la ejecución de comandos del sistema operativo (pg_dump). Requisito obligatorio de infraestructura y recuperación.

    @classmethod
    def execute_database_backup(cls, requested_by: int = None) -> dict:
        from urllib.parse import urlparse

        db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")

        if not db_url or "postgresql" not in db_url:
            raise AppError(
                "El servicio de respaldo solo soporta motores PostgreSQL nativos.",
                status_code=500,
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"skillstat_backup_{timestamp}.sql"

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        backup_dir = os.path.join(base_dir, "data", "backups")
        os.makedirs(backup_dir, exist_ok=True)

        filepath = os.path.join(backup_dir, filename)

        backup_record = BackupRepository.create({
            "filename": filename,
            "filepath": filepath,
            "status": "pending",
            "requested_by": requested_by,
        })

        try:
            # Usamos urlparse para manejar correctamente passwords con caracteres especiales que el split manual no puede resolver.
            parsed = urlparse(db_url)
            user = parsed.username
            password = parsed.password or ""
            host = parsed.hostname
            port = str(parsed.port or 5432)
            db_name = parsed.path.lstrip("/")

            env = os.environ.copy()
            env["PGPASSWORD"] = password

            command = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-F", "c",
                "-f", filepath,
                db_name,
            ]

            subprocess.run(command, env=env, capture_output=True, text=True, check=True)

            file_size = os.path.getsize(filepath)
            BackupRepository.update(
                backup_record.id,
                {"status": "completed", "file_size_bytes": file_size},
            )

            return {"status": "success", "file": filename, "size": file_size}

        except subprocess.CalledProcessError as e:
            BackupRepository.update(backup_record.id, {"status": "failed"})
            raise AppError(
                f"Fallo en ejecucion de pg_dump: {e.stderr}",
                code="BACKUP_ERROR",
            )
        except Exception as e:
            BackupRepository.update(backup_record.id, {"status": "failed"})
            raise AppError(
                f"Error interno durante respaldo: {str(e)}",
                code="BACKUP_ERROR",
            )
