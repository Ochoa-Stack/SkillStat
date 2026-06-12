import hashlib
from app.clients.adzuna_client import AdzunaClient
from app.services.skills_extraction_service import SkillsExtractionService
from app.repositories.job_repository import JobRepository
from app.repositories.skill_repository import SkillRepository
from app.repositories.job_skill_repository import JobSkillRepository
from app.utils.errors import AppError

class IngestionService:
    # Orquestador central del flujo de datos. Conecta el proveedor externo (Adzuna), el motor analítico (NLP) y la capa de persistencia (Repositorios).

    @classmethod
    def run_ingestion(cls, country: str = "mx", what: str = "IT", pages: int = 1) -> dict:
        stats = {"fetched": 0, "processed": 0, "skipped_or_failed": 0}

        # Pre-cargamos las habilidades existentes en memoria para evitar consultas SQL (N+1) por cada habilidad encontrada en cada vacante, minimizando latencia de red.
        known_skills = {skill.name.lower(): skill.id for skill in SkillRepository.get_all()}

        for page in range(1, pages + 1):
            try:
                data = AdzunaClient.get_jobs(country=country, page=page, what=what)
                results = data.get("results", [])
                stats["fetched"] += len(results)
            except AppError:
                # Detenemos paginación si la API externa falla, preservando lo que ya se haya procesado en iteraciones anteriores.
                break

            for item in results:
                cls._process_job(item, known_skills, stats)

        return stats

    @classmethod
    def _process_job(cls, item: dict, known_skills: dict, stats: dict) -> None:
        description = item.get("description", "")
        if not description:
            stats["skipped_or_failed"] += 1
            return

        # Hashing criptográfico para garantizar la idempotencia de la ingesta y evitar guardar la misma vacante si Adzuna la devuelve en días posteriores.
        desc_hash = hashlib.sha256(description.encode("utf-8")).hexdigest()

        title = item.get("title", "Desconocido")
        company = item.get("company", {}).get("display_name", "Confidencial")
        url = item.get("redirect_url", "")
        
        # Guardamos sin location estricta hasta integrar Nominatim, determinando la bandera remote de forma aislada.
        is_remote = "remote" in str(item).lower() or "remoto" in str(item).lower()

        job_data = {
            "title": title[:200],
            "company": company[:200],
            "description": description,
            "url": url,
            "description_hash": desc_hash,
            "remote": is_remote
        }

        job = JobRepository.create(job_data)
        if not job:
            # El repositorio atrapó un error SQL (generalmente violación de UNIQUE del hash)
            stats["skipped_or_failed"] += 1
            return

        # Extracción NLP y vinculación relacional
        extracted_skills = SkillsExtractionService.extract_skills(description)
        for skill_name in extracted_skills:
            skill_id = cls._get_or_create_skill(skill_name, known_skills)
            if skill_id:
                # Inyectamos confidence_score asumiendo certeza determinista del EntityRuler
                JobSkillRepository.create({
                    "job_id": job.id,
                    "skill_id": skill_id,
                    "confidence_score": 0.95
                })

        stats["processed"] += 1

    @classmethod
    def _get_or_create_skill(cls, skill_name: str, known_skills: dict):
        # Mantenemos una única fuente de verdad en memoria durante el ciclo para minimizar I/O contra PostgreSQL.
        skill_key = skill_name.lower()
        if skill_key in known_skills:
            return known_skills[skill_key]
        
        new_skill = SkillRepository.create({
            "name": skill_name,
            "canonical_name": skill_name.upper()
        })
        
        if new_skill:
            known_skills[skill_key] = new_skill.id
            return new_skill.id
            
        return None
