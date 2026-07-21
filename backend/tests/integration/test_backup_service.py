import os
import subprocess
import pytest
from sqlalchemy import select
from app.models.backup import Backup
from app.extensions import db
from app.services.backup_service import BackupService
from app.utils.errors import AppError


def test_execute_database_backup_happy_path(app, db_session):
    """ Happy path de BackupService.execute_database_backup(), su ejecucion real de pg_dump contra skillstat_test, sin ningun mock. Verifica el dict retornado, el registro en BD y el archivo fisico en disco """
    filepath_to_cleanup = None

    try:
        result = BackupService.execute_database_backup(requested_by=None)

        # Aserciones sobre el dict retornado
        assert result["status"] == "success"
        assert result["file"].startswith("skillstat_backup_")
        assert result["file"].endswith(".sql")
        assert result["size"] > 0

        filename = result["file"]

        # Consulta directa al registro en BD (sin metodo nuevo en Repository)
        record = db_session.execute(
            select(Backup).where(Backup.filename == filename)
        ).scalar_one_or_none()

        assert record is not None, f"No se encontro registro en BD para filename={filename}"
        assert record.status == "COMPLETED"
        assert record.user_id is None
        assert record.file_size_bytes is not None
        assert record.file_size_bytes > 0

        # Verificacion del archivo fisico en disco
        filepath_to_cleanup = record.storage_url
        assert os.path.exists(filepath_to_cleanup), (
            f"El archivo fisico no existe en disco: {filepath_to_cleanup}"
        )

        # file_size_bytes en BD debe coincidir exactamente con el tamaño real del archivo
        real_size = os.path.getsize(filepath_to_cleanup)
        assert record.file_size_bytes == real_size, (
            f"file_size_bytes en BD ({record.file_size_bytes}) "
            f"!= tamaño real en disco ({real_size})"
        )

    finally:
        # El archivo .sql vive fuera de la transaccion de Postgres, db_session rollback no lo elimina. Limpieza manual obligatoria.
        if filepath_to_cleanup and os.path.exists(filepath_to_cleanup):
            os.remove(filepath_to_cleanup)


def test_execute_database_backup_pg_dump_failure(app, db_session, monkeypatch):
    """ Ruta de fallo CalledProcessError, subprocess.run lanza CalledProcessError simulando un fallo real de pg_dump. Verifica que execute_database_backup() relanza AppError con code BACKUP_ERROR y que el registro en BD queda en status FAILED. No se genera ningun archivo fisico porque pg_dump nunca se ejecuta realmente """
    # Herramienta de mock, monkeypatch (fixture integrada de pytest, sin dependencia adicional). pytest-mock no esta instalado en el proyecto (no figura en 'requirements.txt').

    def fake_subprocess_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["pg_dump"],
            stderr="mensaje de error simulado de pg_dump"
        )

    monkeypatch.setattr("subprocess.run", fake_subprocess_run)

    with pytest.raises(AppError) as exc_info:
        BackupService.execute_database_backup(requested_by=None)

    # Verifica el code del AppError relanzado
    assert exc_info.value.code == "BACKUP_ERROR"

    # Consulta directa al registro: debe existir (se creo ANTES del mock con status PENDING) y su estado final debe ser FAILED (actualizado por el except CalledProcessError). NOTA: el filename es impredecible, pero solo puede haber un registro con status FAILED creado en esta transaccion aislada, consultamos el mas reciente por created_at.
    record = db_session.execute(
        select(Backup).where(Backup.status == "FAILED").order_by(Backup.created_at.desc())
    ).scalars().first()

    assert record is not None, "No se encontro ningun registro con status FAILED en BD"
    assert record.status == "FAILED"
    assert record.user_id is None


def test_execute_database_backup_generic_exception(app, db_session, monkeypatch):
    """ Ruta de fallo Exception generica: subprocess.run lanza OSError simulando un fallo interno no previsto (no CalledProcessError). Verifica que execute_database_backup() relanza AppError con code BACKUP_ERROR (mismo code que el caso CalledProcessError; confirmado en el codigo de produccion: ambos bloques except usan code='BACKUP_ERROR' sin distincion) y que el registro en BD queda en status FAILED """

    def fake_subprocess_run_oserror(*args, **kwargs):
        raise OSError("fallo interno simulado: binario no disponible")

    monkeypatch.setattr("subprocess.run", fake_subprocess_run_oserror)

    with pytest.raises(AppError) as exc_info:
        BackupService.execute_database_backup(requested_by=None)

    # Ambos bloques except (CalledProcessError y Exception generico) usan code="BACKUP_ERROR". No hay distincion de code entre los dos casos en el codigo de produccion actual.
    assert exc_info.value.code == "BACKUP_ERROR"

    record = db_session.execute(
        select(Backup).where(Backup.status == "FAILED").order_by(Backup.created_at.desc())
    ).scalars().first()

    assert record is not None, "No se encontro ningun registro con status FAILED en BD"
    assert record.status == "FAILED"
    assert record.user_id is None


# Tests de restore_database_backup()

def test_restore_database_backup_not_found(app, db_session):
    """ Caso (a): backup_id inexistente. restore_database_backup() debe lanzar AppError con code NOT_FOUND y status_code 404 """
    with pytest.raises(AppError) as exc_info:
        BackupService.restore_database_backup(backup_id=999999, requested_by=None)

    assert exc_info.value.code == "NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_restore_database_backup_invalid_state(app, db_session):
    """ Caso (b): backup con status PENDING (no COMPLETED). restore_database_backup() debe lanzar AppError con code INVALID_BACKUP_STATE y status_code 422 """
    # Creamos un registro real en BD con status PENDING via insercion directa con db_session. No usamos BackupRepository.create() para evitar acoplarnos a su logica de filtrado.
    pending_backup = Backup(
        filename="test_pending_backup.sql",
        storage_url="/ruta/falsa/test_pending_backup.sql",
        status="PENDING",
        user_id=None,
    )
    db_session.add(pending_backup)
    db_session.commit()

    # Refrescamos para obtener el id asignado por la BD
    db_session.refresh(pending_backup)
    backup_id = pending_backup.id

    with pytest.raises(AppError) as exc_info:
        BackupService.restore_database_backup(backup_id=backup_id, requested_by=None)

    assert exc_info.value.code == "INVALID_BACKUP_STATE"
    assert exc_info.value.status_code == 422


def test_restore_database_backup_file_missing_no_r2(app, db_session):
    """ Caso (c): backup con status COMPLETED pero archivo local inexistente y R2 no configurado. RemoteStorageService.download_backup() retorna False de forma natural en el entorno de testing (R2 no configurado, degradacion suave ya verificada en rama anterior). No se mockea nada. Verifica AppError con code BACKUP_FILE_MISSING y status_code 404 """
    # Ruta que definitivamente no existe en disco
    fake_path = "C:/ruta/absolutamente/inexistente/fake_backup_12345.sql"

    completed_backup = Backup(
        filename="fake_backup_12345.sql",
        storage_url=fake_path,
        status="COMPLETED",
        user_id=None,
        file_size_bytes=1024,
    )
    db_session.add(completed_backup)
    db_session.commit()

    db_session.refresh(completed_backup)
    backup_id = completed_backup.id

    with pytest.raises(AppError) as exc_info:
        BackupService.restore_database_backup(backup_id=backup_id, requested_by=None)

    assert exc_info.value.code == "BACKUP_FILE_MISSING"
    assert exc_info.value.status_code == 404


def test_restore_database_backup_pg_restore_failure(app, db_session, monkeypatch):
    """ Caso (d): pg_dump real (para tener un archivo local legitimo) + pg_restore mockeado con CalledProcessError. El mock es CONDICIONAL: si el primer elemento del comando es 'pg_dump', ejecuta el subprocess.run original; si es 'pg_restore', lanza CalledProcessError simulado. Verifica AppError con code RESTORE_ERROR y status_code 500. El archivo .sql generado por pg_dump se limpia en el finally """
    # Referencia al subprocess.run original, capturada ANTES del monkeypatch
    _original_subprocess_run = subprocess.run

    # Snapshot del directorio de backups ANTES del test para identificar archivos nuevos al limpiar. restore_database_backup() genera DOS archivos fisicos (backup del test + backup de seguridad interno), y el backup de seguridad interno no es visible desde una conexion externa porque vive dentro de la transaccion db_session que luego hace rollback.
    backup_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "backups"
    )
    files_before = set(os.listdir(backup_dir)) if os.path.isdir(backup_dir) else set()

    def conditional_subprocess_run(command, *args, **kwargs):
        if command[0] == "pg_dump":
            # pg_dump debe ejecutarse de verdad para generar un archivo local legitimo
            return _original_subprocess_run(command, *args, **kwargs)
        elif command[0] == "pg_restore":
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=command,
                stderr="mensaje de error simulado de pg_restore"
            )
        # Cualquier otro comando: ejecutar normalmente (fallback defensivo)
        return _original_subprocess_run(command, *args, **kwargs)

    monkeypatch.setattr("subprocess.run", conditional_subprocess_run)

    try:
        # Primero generamos un backup real con pg_dump para tener un archivo local legitimo que restore_database_backup() pueda encontrar en disco (os.path.exists == True).
        real_backup_result = BackupService.execute_database_backup(requested_by=None)

        # Recuperamos el registro real del backup recien generado para obtener su id
        real_backup_record = db_session.execute(
            select(Backup).where(Backup.filename == real_backup_result["file"])
        ).scalar_one_or_none()

        assert real_backup_record is not None, "No se encontro el registro del backup real en BD"
        backup_id = real_backup_record.id

        # Ahora llamamos a restore con ese backup_id. pg_dump se ejecutara de nuevo (backup de seguridad interno) via el mock condicional, y pg_restore fallara con CalledProcessError simulado.
        with pytest.raises(AppError) as exc_info:
            BackupService.restore_database_backup(backup_id=backup_id, requested_by=None)

        assert exc_info.value.code == "RESTORE_ERROR"
        assert exc_info.value.status_code == 500

    finally:
        # Eliminamos todos los archivos .sql nuevos generados durante el test (el backup del test + el backup de seguridad interno de restore), comparando contra el snapshot del directorio tomado antes de empezar.
        if os.path.isdir(backup_dir):
            files_after = set(os.listdir(backup_dir))
            for new_file in files_after - files_before:
                filepath = os.path.join(backup_dir, new_file)
                if os.path.exists(filepath):
                    os.remove(filepath)

