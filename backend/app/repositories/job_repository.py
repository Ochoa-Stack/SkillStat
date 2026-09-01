from app.models.job import Job
from app.repositories.base_repository import BaseRepository
from app.extensions import db

class JobRepository(BaseRepository):
    model = Job

    @classmethod
    def create(cls, data: dict):
        # Capa Anticorrupción (ACL)
        mapped_data = data.copy()
        
        # Traducción de vocabulario
        if "description" in mapped_data:
            mapped_data["raw_description"] = mapped_data.pop("description")
            
        # Eliminación de datos no mapeados en BD
        if "url" in mapped_data:
            del mapped_data["url"]
            
        # Inyectar la fuente de forma centralizada para que los consumidores de job_data no necesiten conocer el detalle del proveedor externo
        mapped_data["source"] = "Adzuna"

        return super().create(mapped_data)


    @classmethod
    def get_by_hash(cls, description_hash: str):
        return db.session.execute(
            db.select(Job).filter_by(description_hash=description_hash)
        ).scalar_one_or_none()
