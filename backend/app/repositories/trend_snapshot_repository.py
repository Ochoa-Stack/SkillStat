from app.repositories.base_repository import BaseRepository
from app.models import TrendSnapshot


class TrendSnapshotRepository(BaseRepository):
    def __init__(self):
        super().__init__(TrendSnapshot)
