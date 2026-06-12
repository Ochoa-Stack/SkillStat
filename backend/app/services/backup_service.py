import os
import subprocess
from datetime import datetime
from flask import current_app
from app.repositories.backup_repository import BackupRepository
from app.utils.errors import AppError

class BackupService:
    # Encapsula la ejecución de comandos del sistema operativo (pg_dump).
    # Requisito obligatorio de infraestructura y recuperación.

    @classmethod
    def execute_database_backup(cls, requested_by: int = None) -> dict:
        db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        
        if not db_url or "postgresql" not in db_url:
            raise AppError("El servicio de respaldo solo soporta motores PostgreSQL nativos.", status_code=500)

        # Generamos un nombre de archivo unívoco por estampa de tiempo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"skillstat_backup_{timestamp}.sql"
        
        # Resolvemos ruta absoluta para evitar que el dump caiga en un directorio volátil
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        backup_dir = os.path.join(base_dir, "data", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        filepath = os.path.join(backup_dir, filename)

        # Inyectamos los metadatos de la operación en estado 'pending'
        backup_record = BackupRepository.create({
            "filename": filename,
            "filepath": filepath,
            "status": "pending",
            "requested_by": requested_by
        })

        try:
            # Parseamos la URL asumiendo formato estandar SQLAlchemy: postgresql://user:pass@host:port/db
            credentials, location = db_url.replace("postgresql://", "").split("@")
            user, password = credentials.split(":")
            host_port, db_name = location.split("/")
            
            host = host_port.split(":")[0]
            port = host_port.split(":")[1] if ":" in host_port else "5432"

            # Inyectar PGPASSWORD en el entorno es la única forma segura de autenticar pg_dump sin exponer credenciales en el historial de comandos del sistema operativo.
            env = os.environ.copy()
            env["PGPASSWORD"] = password

            command = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-F", "c", # Formato custom (comprimido binario) para optimizar I/O
                "-f", filepath,
                db_name
            ]

            process = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
            
            # Actualizamos registro a 'completed' con peso real del archivo
            file_size = os.path.getsize(filepath)
            BackupRepository.update(backup_record.id, {"status": "completed", "file_size_bytes": file_size})
            
            return {"status": "success", "file": filename, "size": file_size}

        except subprocess.CalledProcessError as e:
            BackupRepository.update(backup_record.id, {"status": "failed"})
            raise AppError(f"Fallo en ejecución de pg_dump: {e.stderr}", code="BACKUP_ERROR")
        except Exception as e:
            BackupRepository.update(backup_record.id, {"status": "failed"})
            raise AppError(f"Error interno durante respaldo: {str(e)}", code="BACKUP_ERROR")
