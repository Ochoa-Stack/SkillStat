from app.extensions import db

class BaseRepository:
    # Repositorio genérico que implementa operaciones CRUD estándar
    # para cualquier modelo SQLAlchemy. Utiliza classmethods para evitar
    # la sobrecarga de instanciación en la capa de servicios.
    
    model = None

    @classmethod
    def create(cls, data: dict):
        # Transforma un diccionario DTO en una entidad SQLAlchemy y la persiste.
        # Evita que la capa de Servicios tenga que importar los Modelos de la BD.
        entity = cls.model(**data)
        return cls.save(entity)

    @classmethod
    def save(cls, entity):
        db.session.add(entity)
        try:
            db.session.commit()
            return entity
        except Exception:
            db.session.rollback()
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
