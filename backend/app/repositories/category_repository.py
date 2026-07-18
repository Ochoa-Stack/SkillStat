from app.repositories.base_repository import BaseRepository
from app.models import Category


class CategoryRepository(BaseRepository):
    model = Category
