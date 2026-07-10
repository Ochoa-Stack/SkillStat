from sqlalchemy import inspect
from app.extensions import db

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
        except Exception as e:
            db.session.rollback()
            safe_msg = str(e).encode("ascii", errors="replace").decode("ascii")
            print(f"\n[ERROR DE PERSISTENCIA] Fallo al guardar en BD: {safe_msg}\n")
            return None

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
            return None
        mapper = inspect(cls.model)
        valid_keys = mapper.columns.keys()
        for key, value in data.items():
            if key in valid_keys:
                setattr(entity, key, value)
        return cls.save(entity)
