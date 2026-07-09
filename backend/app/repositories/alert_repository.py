from app.repositories.base_repository import BaseRepository
from app.models import Alert


class AlertRepository(BaseRepository):
    model = Alert

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list:
        # Filtramos directamente en la base de datos para no traer alertas ajenas al usuario en memoria innecesariamente.
        return Alert.query.filter_by(user_id=user_id).all()
