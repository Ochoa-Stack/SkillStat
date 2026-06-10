from app.repositories.base_repository import BaseRepository
from app.models import Alert


class AlertRepository(BaseRepository):
    def __init__(self):
        super().__init__(Alert)
