from app.repositories.base_repository import BaseRepository
from app.models import Backup
from app.extensions import db


class BackupRepository(BaseRepository):
    model = Backup

    @classmethod
    def get_paginated(cls, page: int = 1, per_page: int = 20):
        # Ordenamos descendente por fecha para que el backup más reciente aparezca primero en el panel de administración
        query = db.select(cls.model).order_by(cls.model.created_at.desc())
        total = db.session.execute(
            db.select(db.func.count()).select_from(cls.model)
        ).scalar_one()
        items = db.session.execute(
            query.limit(per_page).offset((page - 1) * per_page)
        ).scalars().all()
        return items, total
