from app.repositories.base_repository import BaseRepository
from app.models import Backup


class BackupRepository(BaseRepository):
    model = Backup
