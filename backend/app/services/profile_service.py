from datetime import datetime, timezone

from app.repositories.user_repository import UserRepository
from app.repositories.user_skill_repository import UserSkillRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.utils.hash import hash_password, verify_password


class ProfileService:

    @classmethod
    def get_skill_gap(cls, user_id: int) -> dict:
        # Cargamos primero las habilidades del usuario, luego el ranking global completo (sin limite), y construimos las dos listas; lo que ya tiene y lo que le falta del top de la industria
        user_skill_rows = UserSkillRepository.get_skills_by_user(user_id)
        user_skill_ids = {row.UserSkill.skill_id for row in user_skill_rows}
        user_skills_by_id = {row.UserSkill.skill_id: row.Skill for row in user_skill_rows}

        # Usamos get_top_skills con un limite alto para obtener el ranking completo disponible
        top_snapshots = TrendSnapshotRepository.get_top_skills(limit=50)

        mis_habilidades = []
        brechas = []

        for rank_index, snapshot in enumerate(top_snapshots, start=1):
            skill_entry = {
                "skill_id": snapshot.skill_id,
                "name": snapshot.skill.name if snapshot.skill else None,
                "demand_count": snapshot.demand_count,
                "ranking_position": rank_index,
            }
            if snapshot.skill_id in user_skill_ids:
                mis_habilidades.append(skill_entry)
            else:
                brechas.append(skill_entry)

        return {
            "mis_habilidades": mis_habilidades,
            "brechas": brechas,
        }

    @classmethod
    def update_profile(cls, user_id: int, data: dict) -> object:
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None

        # Solo actualizamos los campos que llegan en data; los ausentes quedan intactos.
        if data.get("first_name") is not None:
            user.first_name = data["first_name"]
        if data.get("last_name") is not None:
            user.last_name = data["last_name"]
        if "intent" in data:
            # intent puede llegar explicitamente como None para "borrar" el valor
            user.intent = data["intent"]

        return UserRepository.save(user)

    @classmethod
    def change_password(cls, user_id: int, current_password: str, new_password: str) -> None:
        user = UserRepository.get_by_id(user_id)

        # Rechazamos si la cuenta no tiene contrasena propia (solo-OAuth) antes de intentar bcrypt.
        if not user or user.password_hash is None:
            raise ValueError("INVALID_CREDENTIALS")

        if not verify_password(current_password, user.password_hash):
            raise ValueError("INVALID_CREDENTIALS")

        user.password_hash = hash_password(new_password)
        # Actualizamos password_changed_at para que el blocklist callback invalide los tokens anteriores.
        user.password_changed_at = datetime.now(timezone.utc)
        UserRepository.save(user)
