from app.repositories.base_repository import BaseRepository
from app.models import Alert


class AlertRepository(BaseRepository):
    model = Alert

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list:
        # Filtramos directamente en la base de datos para no traer alertas ajenas al usuario en memoria innecesariamente.
        return Alert.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_active(cls) -> list:
        # Filtramos alertas inactivas para no seguir notificando sobre alertas que el usuario ya desactivó. AlertsService.evaluate_and_notify() usaba get_all() sin filtro hasta esta corrección.
        return Alert.query.filter_by(active=True).all()
