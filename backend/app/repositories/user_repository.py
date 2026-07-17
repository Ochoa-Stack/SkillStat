import logging
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.extensions import db
from app.utils.errors import AppError, ConflictError

logger = logging.getLogger(__name__)


class UserRepository:
    # Encapsula el acceso a datos para la entidad User. Aísla las consultas SQLAlchemy de la lógica de negocio.

    @classmethod
    def create(cls, user_data: dict) -> User:
        user = User(**user_data)
        db.session.add(user)
        try:
            db.session.commit()
            return user
        except IntegrityError as e:
            db.session.rollback()
            logger.warning("Violacion de integridad al crear User: %s", str(e))
            raise ConflictError("No se pudo crear el usuario: conflicto de integridad de datos.")
        except Exception as e:
            db.session.rollback()
            logger.error("Fallo inesperado al crear User: %s", str(e))
            raise AppError("Error interno al crear el usuario.", code="DATABASE_ERROR", status_code=500)

    @classmethod
    def get_by_id(cls, user_id: int) -> User:
        return db.session.get(User, user_id)

    @classmethod
    def get_by_email(cls, email: str) -> User:
        # Búsqueda especializada indispensable para el flujo de autenticación y prevención de duplicados
        return db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()

    @classmethod
    def get_all(cls) -> list[User]:
        return db.session.execute(db.select(User)).scalars().all()

    @classmethod
    def get_paginated(cls, page: int = 1, per_page: int = 20):
        # Ordenamos descendente por fecha de creación para que los usuarios más recientes aparezcan primero
        query = db.select(User).order_by(User.created_at.desc())
        total = db.session.execute(
            db.select(db.func.count()).select_from(User)
        ).scalar_one()
        items = db.session.execute(
            query.limit(per_page).offset((page - 1) * per_page)
        ).scalars().all()
        return items, total

    @classmethod
    def save(cls, user: User) -> User:
        # Persiste cambios en una entidad ya existente, como el reseteo de password_hash; no crea un nuevo registro, solo hace commit.
        db.session.add(user)
        try:
            db.session.commit()
            return user
        except IntegrityError as e:
            db.session.rollback()
            logger.warning("Violacion de integridad al guardar User: %s", str(e))
            raise ConflictError("No se pudo guardar el usuario: conflicto de integridad de datos.")
        except Exception as e:
            db.session.rollback()
            logger.error("Fallo inesperado al guardar User: %s", str(e))
            raise AppError("Error interno al guardar el usuario.", code="DATABASE_ERROR", status_code=500)

    @classmethod
    def count_active_admins(cls) -> int:
        # Cuenta administradores activos para proteger contra que una operación deje al sistema sin ningún ADMIN capaz de operar el panel.
        return db.session.execute(
            db.select(db.func.count()).select_from(User).filter_by(
                role="ADMIN", is_active=True
            )
        ).scalar_one()

    @classmethod
    def count_active_admins_for_update(cls) -> int:
        # Version con lock de fila explicito (SELECT ... FOR UPDATE) para proteger contra condiciones de carrera reales: dos requests concurrentes intentando degradar/desactivar a los dos ultimos administradores activos al mismo tiempo. El lock se retiene hasta el commit() de la transaccion actual (el que ya ocurre dentro de save()), forzando que la segunda request espere a que la primera termine antes de leer un conteo actualizado.
        # Nota de implementacion: with_for_update() no es compatible directamente con func.count() como subquery en SQLAlchemy 2.x, por lo que se aplica FOR UPDATE sobre la query de filas y se cuenta el resultado en Python (equivalente semanticamente).
        rows = db.session.execute(
            db.select(User.id).filter_by(
                role="ADMIN", is_active=True
            ).with_for_update()
        ).all()
        return len(rows)
