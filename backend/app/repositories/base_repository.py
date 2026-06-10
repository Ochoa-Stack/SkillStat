from app.extensions import db


class BaseRepository:
    def __init__(self, model):
        self.model = model

    def get_all(self):
        return db.session.query(self.model).all()

    def get_by_id(self, id):
        return db.session.get(self.model, id)

    def create(self, data):
        # Protegemos la transacción con un bloque de manejo de errores para garantizar que una falla en la escritura no deje bloqueada la sesión de la base de datos
        try:
            instance = self.model(**data)
            db.session.add(instance)
            db.session.commit()
            return instance
        except Exception as e:
            db.session.rollback()
            raise e

    def update(self, id, data):
        try:
            instance = self.get_by_id(id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                db.session.commit()
            return instance
        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self, id):
        try:
            instance = self.get_by_id(id)
            if instance:
                db.session.delete(instance)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e
