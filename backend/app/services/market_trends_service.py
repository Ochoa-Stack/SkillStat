import pandas as pd
from datetime import datetime, timezone
from app.repositories.job_skill_repository import JobSkillRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.utils.errors import AppError

class MarketTrendsService:
    # Motor de procesamiento de datos analíticos. Aísla las operaciones vectoriales pesadas del resto del sistema para evitar cuellos de botella en el hilo principal de Flask.

    @classmethod
    def generate_snapshots(cls) -> int:
        raw_data = JobSkillRepository.get_all()
        
        if not raw_data:
            return 0

        # Transformación a DataFrame para aprovechar las rutinas en C subyacentes de pandas, erradicando la necesidad de bucles for anidados en Python puro.
        df = pd.DataFrame([{
            "skill_id": item.skill_id,
            "job_id": item.job_id,
            "confidence": item.confidence_score
        } for item in raw_data])

        # Agrupación y conteo vectorial.
        # Extraemos el volumen de demanda absoluto por habilidad tecnológica.
        trends = df.groupby("skill_id").size().reset_index(name="demand_count")
        
        today = datetime.now(timezone.utc).date()
        snapshots_created = 0

        for _, row in trends.iterrows():
            # Volcamos las métricas agregadas a la tabla de snapshots para que el endpoint del Panorama realice lecturas directas en lugar de recalcular.
            snapshot_data = {
                "skill_id": int(row["skill_id"]),
                "city_id": None,
                "date": today,
                "demand_count": int(row["demand_count"])
            }
            
            # Delegamos al Repositorio el manejo de la restricción UNIQUE(skill_id, city_id, date) mediante los bloques try/except con rollback previamente configurados.
            result = TrendSnapshotRepository.create(snapshot_data)
            if result:
                snapshots_created += 1

        return snapshots_created
