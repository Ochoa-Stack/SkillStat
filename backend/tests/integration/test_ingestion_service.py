import pytest
from unittest.mock import MagicMock

from app.services.ingestion_service import IngestionService, MEXICO_NACIONAL_CITY_ID
from app.utils.errors import AppError

def test_run_ingestion_stops_on_apperror_and_preserves_stats(monkeypatch):
    """ run_ingestion detiene la paginación cuando AdzunaClient.get_jobs lanza AppError, preservando las estadísticas acumuladas hasta ese punto. """
    mock_get_jobs = MagicMock()
    # Primera página devuelve 2 jobs. Segunda página lanza AppError.
    mock_get_jobs.side_effect = [
        {"results": [{"description": "Job 1"}, {"description": "Job 2"}]},
        AppError("API Error")
    ]
    monkeypatch.setattr("app.services.ingestion_service.AdzunaClient.get_jobs", mock_get_jobs)
    
    mock_get_all_skills = MagicMock(return_value=[])
    monkeypatch.setattr("app.services.ingestion_service.SkillRepository.get_all", mock_get_all_skills)
    
    mock_process_job = MagicMock()
    monkeypatch.setattr("app.services.ingestion_service.IngestionService._process_job", mock_process_job)

    stats = IngestionService.run_ingestion(pages=3)
    
    # Se intentaron 2 páginas antes de detenerse
    assert mock_get_jobs.call_count == 2
    # El loop interno procesó los 2 jobs de la página 1 antes de detenerse
    assert mock_process_job.call_count == 2
    assert stats["fetched"] == 2

def test_process_job_increments_duplicates_when_hash_exists(monkeypatch):
    """ _process_job incrementa stats['duplicates'] y no llama a JobRepository.create cuando JobRepository.get_by_hash ya encuentra un hash existente. """
    mock_get_by_hash = MagicMock(return_value={"id": 1}) # Any truthy value implies it exists
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.get_by_hash", mock_get_by_hash)
    
    mock_create_job = MagicMock()
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.create", mock_create_job)

    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    item = {"description": "This is a duplicate job"}
    IngestionService._process_job(item, {}, stats)
    
    assert stats["duplicates"] == 1
    mock_get_by_hash.assert_called_once()
    mock_create_job.assert_not_called()

def test_process_job_increments_errors_on_empty_description(monkeypatch):
    """ _process_job incrementa stats['errors'] cuando la descripción del job está vacía, sin llegar a calcular el hash ni tocar el repositorio. """
    mock_get_by_hash = MagicMock()
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.get_by_hash", mock_get_by_hash)

    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    # Missing description
    IngestionService._process_job({}, {}, stats)
    
    assert stats["errors"] == 1
    mock_get_by_hash.assert_not_called()

def test_process_job_extracts_last_area_as_raw_location(monkeypatch):
    """ _process_job extrae correctamente el último elemento de location.area como raw_location antes de resolver la ciudad. """
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.get_by_hash", MagicMock(return_value=None))
    
    mock_job = MagicMock()
    mock_job.id = 99
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.create", MagicMock(return_value=mock_job))
    monkeypatch.setattr("app.services.ingestion_service.SkillsExtractionService.extract_skills", MagicMock(return_value=[]))
    
    mock_resolve_city = MagicMock(return_value=(1, "Mock City"))
    monkeypatch.setattr("app.services.ingestion_service.IngestionService._resolve_city", mock_resolve_city)

    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    item = {
        "description": "Job desc",
        "location": {
            "area": ["Country", "State", "CitySpecific"]
        }
    }
    
    IngestionService._process_job(item, {}, stats)
    
    mock_resolve_city.assert_called_once_with("CitySpecific", stats, verbose=False)

def test_resolve_city_returns_fallback(monkeypatch):
    """ _resolve_city retorna MEXICO_NACIONAL_CITY_ID y registra stats['fallback'] cuando CityRepository.get_or_create_city retorna (None, False). """
    monkeypatch.setattr("app.services.ingestion_service.CityService.get_or_create_city", MagicMock(return_value=(None, False)))
    
    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    city_id, label = IngestionService._resolve_city("UnknownPlace", stats)
    
    assert city_id == MEXICO_NACIONAL_CITY_ID
    assert stats["fallback"] == 1
    assert stats["cities_created"] == 0

def test_resolve_city_returns_id_and_increments_created_when_new(monkeypatch):
    """ _resolve_city retorna el id real y registra stats['cities_created'] cuando CityRepository.get_or_create_city retorna una ciudad nueva (created=True). """
    mock_city = MagicMock()
    mock_city.id = 42
    mock_city.name = "TestCity"
    mock_city.state = "TestState"
    
    monkeypatch.setattr("app.services.ingestion_service.CityService.get_or_create_city", MagicMock(return_value=(mock_city, True)))
    
    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    city_id, label = IngestionService._resolve_city("TestCity", stats)
    
    assert city_id == 42
    assert stats["cities_created"] == 1
    assert stats["fallback"] == 0

def test_get_or_create_skill_reuses_id_case_insensitive(monkeypatch):
    """ _get_or_create_skill reutiliza el id ya presente en known_skills sin llamar a SkillRepository.create cuando el skill ya existe en el diccionario en memoria (verificar case-insensitive). """
    mock_create_skill = MagicMock()
    monkeypatch.setattr("app.services.ingestion_service.SkillRepository.create", mock_create_skill)

    known_skills = {"python": 100}
    
    # Testing case insensitivity: the dictionary key is "python", we pass "PyThOn"
    skill_id = IngestionService._get_or_create_skill("PyThOn", known_skills)
    
    assert skill_id == 100
    mock_create_skill.assert_not_called()

def test_is_remote_ignores_company_name_containing_remote(monkeypatch):
    """ is_remote solo examina title y description. Un job cuya empresa se llama "RemoteWorks Solutions" pero cuyo título y descripción son presenciales NO debe marcarse como remoto. Verifica el comportamiento correcto tras la corrección del bug. """
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.get_by_hash", MagicMock(return_value=None))
    
    mock_job = MagicMock()
    mock_job.id = 99
    mock_create_job = MagicMock(return_value=mock_job)
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.create", mock_create_job)
    monkeypatch.setattr("app.services.ingestion_service.SkillsExtractionService.extract_skills", MagicMock(return_value=[]))
    monkeypatch.setattr("app.services.ingestion_service.CityService.get_or_create_city", MagicMock(return_value=(None, False)))

    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    # Empresa con "Remote" en el nombre, pero título y descripción completamente presenciales.
    item = {
        "title": "Backend Developer (On-site)",
        "description": "We need an on-site backend developer to work in our office in Monterrey.",
        "company": {
            "display_name": "RemoteWorks Solutions"
        }
    }
    
    IngestionService._process_job(item, {}, stats)
    
    job_data_passed = mock_create_job.call_args[0][0]
    
    # El nombre de la empresa NO debe influir en la detección de modalidad.
    assert job_data_passed["remote"] is False


def test_is_remote_detects_genuine_remote_in_description(monkeypatch):
    """ is_remote detecta correctamente 'remoto' como palabra completa dentro de la descripción. Caso positivo genuino: la modalidad remota sí está mencionada en el texto de la vacante. """
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.get_by_hash", MagicMock(return_value=None))
    
    mock_job = MagicMock()
    mock_job.id = 100
    mock_create_job = MagicMock(return_value=mock_job)
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.create", mock_create_job)
    monkeypatch.setattr("app.services.ingestion_service.SkillsExtractionService.extract_skills", MagicMock(return_value=[]))
    monkeypatch.setattr("app.services.ingestion_service.CityService.get_or_create_city", MagicMock(return_value=(None, False)))

    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    item = {
        "title": "Desarrollador Backend",
        "description": "Puesto 100% remoto, no requiere presencia en oficina. Trabajo desde casa.",
        "company": {"display_name": "TechCorp"}
    }
    
    IngestionService._process_job(item, {}, stats)
    
    job_data_passed = mock_create_job.call_args[0][0]
    
    # La palabra 'remoto' en la descripción debe marcar el job como remoto.
    assert job_data_passed["remote"] is True


def test_is_remote_does_not_match_partial_word_containing_remoto(monkeypatch):
    """ is_remote usa \\b (límite de palabra), por lo que una cadena que contenga 'remoto' como subcadena de otra palabra (ej. 'remotorizado') NO debe disparar un falso positivo. """
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.get_by_hash", MagicMock(return_value=None))
    
    mock_job = MagicMock()
    mock_job.id = 101
    mock_create_job = MagicMock(return_value=mock_job)
    monkeypatch.setattr("app.services.ingestion_service.JobRepository.create", mock_create_job)
    monkeypatch.setattr("app.services.ingestion_service.SkillsExtractionService.extract_skills", MagicMock(return_value=[]))
    monkeypatch.setattr("app.services.ingestion_service.CityService.get_or_create_city", MagicMock(return_value=(None, False)))

    stats = {"fetched": 0, "processed": 0, "duplicates": 0, "errors": 0, "cities_created": 0, "fallback": 0}
    
    # 'remotorizado' contiene la subcadena 'remoto' pero no es la palabra 'remoto'.
    item = {
        "title": "Tecnico Electrico",
        "description": "Se requiere conocimiento en sistemas remotorizado y control de motores.",
        "company": {"display_name": "ElectroCorp"}
    }
    
    IngestionService._process_job(item, {}, stats)
    
    job_data_passed = mock_create_job.call_args[0][0]
    
    # 'remotorizado' no debe confundirse con la palabra 'remoto'.
    assert job_data_passed["remote"] is False
