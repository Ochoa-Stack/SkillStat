from app.repositories.base_repository import BaseRepository
from app.models import Backup


class BackupRepository(BaseRepository):
    def __init__(self):
        super().__init__(Backup)
