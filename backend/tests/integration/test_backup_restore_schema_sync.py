"""
Test de integracion: auto-sincronizacion de esquema tras restore.

Advertencia Crítica de Diseño:
Este test NO usa db_session ni depende del aislamiento transaccional para su limpieza. Las operaciones DDL de Alembic (downgrade/upgrade) se ejecutan en conexiones independientes, un rollback de transaccion ORM NO revierte un ALTER TABLE ya aplicado por Alembic. El cleanup es manual y explicito en el bloque finally, con verificacion activa del estado final.

El test replica el incidente historico verificado manualmente por Elias; Downgrade real de la BD un paso hacia atras (esquema viejo). pg_dump sobre el esquema viejo -> archivo .sql viejo. Upgrade de vuelta al head actual. Insertar registro Backup apuntando al .sql viejo. Llamar restore_database_backup(), que aplica pg_restore + upgrade(). Confirmar que el esquema quedo en head sin intervencion manual """
import os
import subprocess
import pytest
from urllib.parse import urlparse
from sqlalchemy import inspect as sa_inspect, text
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask_migrate import upgrade, downgrade
from app.models.backup import Backup
from app.extensions import db
from app.services.backup_service import BackupService


def _get_alembic_config(app):
    """ Retorna el AlembicConfig registrado via flask_migrate en el contexto activo """
    return app.extensions["migrate"].migrate.get_config()


def _get_db_current_revision(engine):
    """ Consulta la revision actual de alembic_version en la base de datos """
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        return ctx.get_current_revision()


def _get_alembic_head(app):
    """ Retorna el head actual del ScriptDirectory de Alembic (desde el codigo, no desde la BD) """
    config = _get_alembic_config(app)
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    assert len(heads) == 1, (
        f"Se esperaba exactamente 1 head de Alembic, se encontraron: {heads}. "
        "El test asume una cadena lineal de migraciones."
    )
    return heads[0]


def _build_pg_dump_command(db_url, output_filepath):
    """ Construye el comando pg_dump usando el mismo patron que backup_service.py """
    parsed = urlparse(db_url)
    user = parsed.username
    host = parsed.hostname
    port = str(parsed.port or 5432)
    db_name = parsed.path.lstrip("/")
    return (
        ["pg_dump", "-h", host, "-p", port, "-U", user, "-F", "c", "-f", output_filepath, db_name],
        parsed.password or "",
    )


def test_restore_triggers_automatic_schema_sync(app):
    """ Verifica que restore_database_backup() re-sincroniza el esquema de la BD automaticamente tras un pg_restore que revierte a un esquema viejo, sin requerir intervencion manual

    NOTA: No recibe db_session, gestiona su propia conexion y cleanup DDL """
    backup_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "backups"
    )

    with app.app_context():
        expected_head = _get_alembic_head(app)
        db_url = app.config["SQLALCHEMY_DATABASE_URI"]

        files_before = set(os.listdir(backup_dir)) if os.path.isdir(backup_dir) else set()

        inserted_backup_id = None

        try:
            downgrade(revision="-1")

            revision_after_downgrade = _get_db_current_revision(db.engine)
            assert revision_after_downgrade != expected_head, (
                "El downgrade no produjo ningun cambio -- la BD ya estaba en una "
                "revision anterior al head. Verificar el estado de skillstat_test."
            )

            # NO usamos BackupService.execute_database_backup() porque ese metodo inserta un registro Backup via ORM, lo que requiere el esquema actual completo para funcionar correctamente. pg_dump crudo evita esa dependencia.
            os.makedirs(backup_dir, exist_ok=True)
            old_sql_filename = f"test_schema_sync_old_schema.sql"
            old_sql_path = os.path.join(backup_dir, old_sql_filename)

            command, password = _build_pg_dump_command(db_url, old_sql_path)
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            subprocess.run(command, env=env, capture_output=True, text=True, check=True)

            assert os.path.exists(old_sql_path), "pg_dump no genero el archivo .sql esperado"
            old_sql_size = os.path.getsize(old_sql_path)
            assert old_sql_size > 0, "El archivo .sql generado por pg_dump esta vacio"

            upgrade()

            revision_after_reupgrade = _get_db_current_revision(db.engine)
            assert revision_after_reupgrade == expected_head, (
                f"El upgrade de vuelta al head fallo: se esperaba {expected_head}, "
                f"se obtuvo {revision_after_reupgrade}."
            )

            # Insertamos el registro de backup evadiendo BackupRepository para no acoplar el test a la logica de filtrado de columnas del repositorio.
            backup_record = Backup(
                filename=old_sql_filename,
                storage_url=old_sql_path,
                status="COMPLETED",
                user_id=None,
                file_size_bytes=old_sql_size,
            )
            db.session.add(backup_record)
            db.session.commit()
            db.session.refresh(backup_record)
            inserted_backup_id = backup_record.id

            result = BackupService.restore_database_backup(
                backup_id=inserted_backup_id,
                requested_by=None,
            )

            assert result["status"] == "success", (
                f"restore_database_backup() no retorno status='success': {result}"
            )

            # Si restore_database_backup() resincronizo el esquema correctamente, este assert debe pasar sin que nosotros llamemos upgrade() aqui, es la prueba real de que el mecanismo automatico funciono.
            revision_after_restore = _get_db_current_revision(db.engine)
            assert revision_after_restore == expected_head, (
                f"El esquema NO fue resincronizado automaticamente por restore_database_backup(). "
                f"Se esperaba {expected_head}, se obtuvo {revision_after_restore}. "
                "La llamada automatica a upgrade() dentro del servicio no funciono."
            )

            # Validamos que los cambios del head actual de Alembic estan realmente en la base de datos usando el inspector de SQLAlchemy en vez de cadenas de texto fijas.
            inspector = sa_inspect(db.engine)
            columns = {col["name"] for col in inspector.get_columns("backups")}
            assert "file_size_bytes" in columns, (
                f"La columna 'file_size_bytes' no existe en la tabla 'backups'. "
                f"Columnas actuales: {columns}. "
                "El esquema no fue correctamente resincronizado al head."
            )

        finally:
            # Intentamos resincronizar el esquema aunque el test ya haya fallado, para no dejar skillstat_test en un estado inconsistente para los siguientes tests.
            try:
                upgrade()
            except Exception as cleanup_upgrade_err:
                # No silenciamos este error, lo relanzamos para que el test falle con un mensaje explicito sobre el estado del entorno.
                raise AssertionError(
                    f"CLEANUP FALLIDO: No se pudo dejar skillstat_test en el head "
                    f"'{expected_head}' tras el test. Se requiere intervencion manual: "
                    f"ejecutar 'flask db upgrade' desde la terminal. "
                    f"Error: {cleanup_upgrade_err}"
                ) from cleanup_upgrade_err

            final_revision = _get_db_current_revision(db.engine)
            if final_revision != expected_head:
                raise AssertionError(
                    f"CLEANUP FALLIDO: skillstat_test quedo en revision '{final_revision}' "
                    f"en vez del head esperado '{expected_head}'. "
                    "Se requiere intervencion manual: ejecutar 'flask db upgrade'."
                )

            if inserted_backup_id is not None:
                try:
                    record = db.session.get(Backup, inserted_backup_id)
                    if record:
                        db.session.delete(record)
                        db.session.commit()
                except Exception:
                    # El registro es de test., si ya fue limpiado por rollback, ignoramos el fallo.
                    db.session.rollback()

            if os.path.isdir(backup_dir):
                files_after = set(os.listdir(backup_dir))
                for new_file in files_after - files_before:
                    filepath = os.path.join(backup_dir, new_file)
                    if os.path.exists(filepath):
                        os.remove(filepath)
