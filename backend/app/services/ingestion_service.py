import hashlib
import click
from flask import current_app
from app.clients.adzuna_client import AdzunaClient
from app.services.skills_extraction_service import SkillsExtractionService
from app.repositories.job_repository import JobRepository
from app.repositories.skill_repository import SkillRepository
from app.repositories.job_skill_repository import JobSkillRepository
from app.repositories.city_repository import CityRepository
from app.utils.errors import AppError

# ID de "México Nacional", fila de fallback cuando la ubicación cruda no puede geocodificarse. Usamos una constante en lugar de una query extra por ejecución porque la fila es de solo lectura y su ID es estable
MEXICO_NACIONAL_CITY_ID = 1

class IngestionService:
    # Orquestador central del flujo de datos. Conecta el proveedor externo (Adzuna), el motor analítico (NLP) y la capa de persistencia (Repositorios).

    @classmethod
    def run_ingestion(cls, country: str = "mx", what: str = "software developer", pages: int = 1, verbose: bool = False) -> dict:
        stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}

        # Pre-cargamos las habilidades existentes en memoria para evitar consultas SQL (N+1) por cada habilidad encontrada en cada vacante, minimizando latencia de red.
        known_skills = {skill.name.lower(): skill.id for skill in SkillRepository.get_all()}

        for page in range(1, pages + 1):
            try:
                data = AdzunaClient.get_jobs(country=country, page=page, what=what)
                results = data.get("results", [])
                stats["fetched"] += len(results)
                if verbose:
                    click.echo(f"[Pagina {page}] {len(results)} vacantes recibidas de Adzuna.")
            except AppError:
                # Detenemos paginación si la API externa falla, preservando lo que ya se haya procesado en iteraciones anteriores.
                if verbose:
                    click.echo(f"[Pagina {page}] Error al contactar Adzuna, deteniendo ingesta.")
                break

            for item in results:
                cls._process_job(item, known_skills, stats, verbose=verbose)

        return stats

    @classmethod
    def _process_job(cls, item: dict, known_skills: dict, stats: dict, verbose: bool = False) -> None:
        description = item.get("description", "")
        if not description:
            stats["errors"] += 1
            return

        # Hashing criptográfico para garantizar la idempotencia de la ingesta y evitar guardar la misma vacante si Adzuna la devuelve en días posteriores.
        desc_hash = hashlib.sha256(description.encode("utf-8")).hexdigest()
        
        # Validar duplicados ANTES de geocodificar o instanciar objetos, para evitar excepciones de BD y transacciones descartadas
        if JobRepository.get_by_hash(desc_hash):
            stats["duplicates"] += 1
            return

        title = item.get("title", "Desconocido")
        company = item.get("company", {}).get("display_name", "Confidencial")
        url = item.get("redirect_url", "")
        
        # Guardamos sin location estricta hasta integrar Nominatim, determinando la bandera remote de forma aislada.
        is_remote = "remote" in str(item).lower() or "remoto" in str(item).lower()

        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")

        # El campo location.area de Adzuna es una lista [país, estado, ciudad, ...] ordenada de más general a más específico. Tomamos el último elemento porque es siempre la entidad más concreta disponible, que coincide mejor con lo que Nominatim espera
        location_area = item.get("location", {}).get("area", [])
        raw_location = location_area[-1] if location_area else ""

        city_id, city_label = cls._resolve_city(raw_location, stats, verbose=verbose)

        if verbose:
            click.echo(f"  Vacante: {title[:60]} | Ubicacion: '{raw_location}' -> {city_label}")

        job_data = {
            "title": title,
            "company": company,
            "description": description,
            "url": url,
            "description_hash": desc_hash,
            "remote": is_remote,
            "city_id": city_id,
            # Capturamos los rangos salariales cuando Adzuna los incluye. Muchas vacantes no los declaran, por eso permitimos nulos
            "salary_min": float(salary_min) if salary_min is not None else None,
            "salary_max": float(salary_max) if salary_max is not None else None,
        }

        job = JobRepository.create(job_data)
        if not job:
            # El repositorio atrapó un error SQL (diferente a duplicado, ya que esos los validamos antes)
            stats["errors"] += 1
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
    def _resolve_city(cls, raw_location: str, stats: dict, verbose: bool = False):
        """Resuelve la ubicación cruda de Adzuna a una fila de la tabla cities.
        Devuelve (city_id, label_para_log). Usa "México Nacional" como fallback cuando la geocodificación falla o la ubicación está vacía, para garantizar que city_id nunca quede nulo"""
        city, created = CityRepository.get_or_create_city(raw_location) if raw_location else (None, False)

        if city:
            if created:
                stats["cities_created"] += 1
            return city.id, f"Ciudad: {city.name} ({city.state})"
        else:
            stats["fallback"] += 1
            return MEXICO_NACIONAL_CITY_ID, "fallback → México Nacional"

    @classmethod
    def _get_or_create_skill(cls, skill_name: str, known_skills: dict):
        # Mantenemos una única fuente centralizada en memoria durante el ciclo para minimizar I/O contra PostgreSQL
        skill_key = skill_name.lower()
        if skill_key in known_skills:
            return known_skills[skill_key]
        
        new_skill = SkillRepository.create({
            "name": skill_name,
            "canonical_name": skill_name.upper(),
            # Asignamos la categoría General como fallback para habilidades detectadas por el NLP que aún no tienen clasificación formal
            "category_id": 1,
        })
        
        if new_skill:
            known_skills[skill_key] = new_skill.id
            return new_skill.id
            
        return None
