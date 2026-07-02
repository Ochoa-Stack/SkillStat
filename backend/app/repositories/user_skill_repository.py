from app.extensions import db
from app.models.user_skill import UserSkill
from app.models.skill import Skill
from sqlalchemy.exc import IntegrityError


class UserSkillRepository:
    # Encapsula el acceso a datos de la tabla de relacion usuario-habilidad. Usa metodos idem potentes para que el controlador no tenga que verificar existencia antes de operar.

    @classmethod
    def get_skills_by_user(cls, user_id: int) -> list:
        # Hacemos join con Skill para traer el nombre canonico en una sola consulta, evitando N+1 queries.
        return db.session.execute(
            db.select(UserSkill, Skill)
            .join(Skill, Skill.id == UserSkill.skill_id)
            .filter(UserSkill.user_id == user_id)
        ).all()

    @classmethod
    def add_skill(cls, user_id: int, skill_id: int) -> bool:
        # Intentamos insertar; si ya existe la llave compuesta, atrapamos la excepcion de integridad y devolvemos False sin lanzar, para que el endpoint POST sea naturalmente idempotente.
        entry = UserSkill(user_id=user_id, skill_id=skill_id)
        db.session.add(entry)
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    @classmethod
    def remove_skill(cls, user_id: int, skill_id: int) -> bool:
        # Eliminamos si existe, sin error si no existe, para que DELETE sea idempotente.
        entry = db.session.get(UserSkill, (user_id, skill_id))
        if entry:
            db.session.delete(entry)
            db.session.commit()
            return True
        return False
