import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect
from app.extensions import db
from app.utils.errors import AppError, ConflictError

logger = logging.getLogger(__name__)


class BaseRepository:
    # Repositorio genérico con soporte de instanciación dinámica y segura
    model = None

    @classmethod
    def create(cls, data: dict):
        # Extraemos solo las llaves que corresponden a columnas reales en la base de datos, ignorando cualquier metadato extra proveniente de APIs externas o DTOs mal alineados
        mapper = inspect(cls.model)
        valid_keys = mapper.columns.keys()

        filtered_data = {k: v for k, v in data.items() if k in valid_keys}

        entity = cls.model(**filtered_data)
        return cls.save(entity)

    @classmethod
    def save(cls, entity):
        db.session.add(entity)
        try:
            db.session.commit()
            return entity
        except IntegrityError as e:
            db.session.rollback()
            logger.warning(
                "Violacion de integridad al guardar %s: %s",
                cls.model.__name__, str(e)
            )
            raise ConflictError(
                f"No se pudo guardar {cls.model.__name__}: conflicto de integridad de datos."
            )
        except Exception as e:
            db.session.rollback()
            logger.error(
                "Fallo inesperado al guardar %s: %s",
                cls.model.__name__, str(e)
            )
            raise AppError(
                f"Error interno al guardar {cls.model.__name__}.",
                code="DATABASE_ERROR",
                status_code=500,
            )

    @classmethod
    def get_by_id(cls, entity_id: int):
        return db.session.get(cls.model, entity_id)

    @classmethod
    def get_all(cls):
        return db.session.execute(db.select(cls.model)).scalars().all()

    @classmethod
    def delete(cls, entity_id: int) -> bool:
        entity = cls.get_by_id(entity_id)
        if entity:
            db.session.delete(entity)
            db.session.commit()
            return True
        return False

    @classmethod
    def update(cls, entity_id: int, data: dict):
        # Localizamos la entidad, aplicamos solo las llaves que corresponden a columnas reales (mismo criterio que create) y persistimos vía save para mantener el mismo contrato de commit/rollback.
        entity = cls.get_by_id(entity_id)
        if not entity:
            # "No encontrado" es semánticamente distinto a un fallo de persistencia -- no se convierte en excepción
            return None
        mapper = inspect(cls.model)
        valid_keys = mapper.columns.keys()
        for key, value in data.items():
            if key in valid_keys:
                setattr(entity, key, value)
        return cls.save(entity)
