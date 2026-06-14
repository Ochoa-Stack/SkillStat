from app.models.job import Job
from app.repositories.base_repository import BaseRepository

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
            
        # Protección contra StringDataRightTruncation
        mapped_data["source"] = "Adzuna"
        
        if mapped_data.get("title"):
            mapped_data["title"] = str(mapped_data["title"])[:150]
        if mapped_data.get("company"):
            mapped_data["company"] = str(mapped_data["company"])[:100]
            
        return super().create(mapped_data)
