import requests
from flask import current_app
from app.utils.errors import AppError

class AdzunaClient:
    # Encapsulamos la comunicación con Adzuna para aislar la lógica HTTP del resto del sistema. Si Adzuna cambia su API, solo modificamos este archivo.
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    @classmethod
    def get_jobs(cls, country: str = "mx", page: int = 1, what: str = "IT", where: str = "") -> dict:
        app_id = current_app.config.get("ADZUNA_APP_ID")
        app_key = current_app.config.get("ADZUNA_APP_KEY")

        if not app_id or not app_key:
            raise AppError("Credenciales de Adzuna no configuradas.", status_code=500)

        url = f"{cls.BASE_URL}/{country}/search/{page}"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": what,
            "where": where,
            "results_per_page": 50,
            "content-type": "application/json"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # Levantamos una excepción de negocio pura en lugar de un error HTTP genérico
            raise AppError(f"Error al comunicar con Adzuna: {str(e)}", code="EXTERNAL_API_ERROR")
