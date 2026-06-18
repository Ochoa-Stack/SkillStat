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

        # Incluimos salary_min y salary_max de la vacante asociada para poder calcular el salario promedio por habilidad en el mismo paso que calculamos la demanda, evitando una segunda consulta.
        df = pd.DataFrame([{
            "skill_id": item.skill_id,
            "job_id": item.job_id,
            "confidence": item.confidence_score,
            "salary_min": float(item.job.salary_min) if item.job and item.job.salary_min is not None else None,
            "salary_max": float(item.job.salary_max) if item.job and item.job.salary_max is not None else None,
        } for item in raw_data])

        # Calculamos el punto medio del rango salarial por vacante. mean(axis=1, skipna=True) toma el unico valor disponible si solo uno de los dos extremos esta presente.
        df["salary_mid"] = df[["salary_min", "salary_max"]].mean(axis=1, skipna=True)

        trends = df.groupby("skill_id").agg(
            demand_count=("job_id", "size"),
            avg_salary=("salary_mid", "mean"),
        ).reset_index()

        today = datetime.now(timezone.utc).date()
        snapshots_created = 0

        for _, row in trends.iterrows():
            avg_salary_value = row["avg_salary"]
            # pandas representa la ausencia de datos como NaN, que no es serializable ni almacenable como None directamente en SQL.
            if pd.isna(avg_salary_value):
                avg_salary_value = None
            else:
                avg_salary_value = float(avg_salary_value)

            snapshot_data = {
                "skill_id": int(row["skill_id"]),
                "city_id": 1,
                "date": today,
                "demand_count": int(row["demand_count"]),
                "avg_salary": avg_salary_value,
            }

            result = TrendSnapshotRepository.create(snapshot_data)
            if result:
                snapshots_created += 1

        return snapshots_created
