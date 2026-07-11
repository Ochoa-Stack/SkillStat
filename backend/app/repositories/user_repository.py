from app.models.user import User
from app.extensions import db

class UserRepository:
    # Encapsula el acceso a datos para la entidad User. Aísla las consultas SQLAlchemy de la lógica de negocio.

    @classmethod
    def create(cls, user_data: dict) -> User:
        user = User(**user_data)
        db.session.add(user)
        try:
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            return None

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
        except Exception:
            db.session.rollback()
            return None
