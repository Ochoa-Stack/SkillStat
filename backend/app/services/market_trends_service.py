import pandas as pd
from datetime import datetime, timezone, timedelta
from app.repositories.job_skill_repository import JobSkillRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.utils.errors import AppError

class MarketTrendsService:
    # Motor de procesamiento de datos analíticos. Aísla las operaciones vectoriales pesadas del resto del sistema para evitar cuellos de botella en el hilo principal de Flask

    @classmethod
    def generate_snapshots(cls) -> int:
        raw_data = JobSkillRepository.get_active(days=30)

        if not raw_data:
            return 0

        # Incluimos salary_min, salary_max y city_id de la vacante asociada para calcular demanda y salario promedio por habilidad y ciudad en un solo paso
        df = pd.DataFrame([{
            "skill_id": item.skill_id,
            "job_id": item.job_id,
            "confidence": item.confidence_score,
            # Usamos city_id=1 (México Nacional) como fallback para vacantes sin geocodificación para no perder esas métricas de la agregación
            "city_id": item.job.city_id if item.job and item.job.city_id is not None else 1,
            "salary_min": float(item.job.salary_min) if item.job and item.job.salary_min is not None else None,
            "salary_max": float(item.job.salary_max) if item.job and item.job.salary_max is not None else None,
        } for item in raw_data])

        # Calculamos el punto medio del rango salarial por vacante. mean(axis=1, skipna=True) toma el unico valor disponible si solo uno de los dos extremos esta presente
        df["salary_mid"] = df[["salary_min", "salary_max"]].mean(axis=1, skipna=True)

        # Agrupamos por habilidad Y ciudad para que /geo pueda mostrar distribución geográfica real en lugar de todo colapsado a México Nacional
        trends = df.groupby(["skill_id", "city_id"]).agg(
            demand_count=("job_id", "size"),
            avg_salary=("salary_mid", "mean"),
        ).reset_index()

        today = datetime.now(timezone.utc).date()
        snapshots_created = 0

        for _, row in trends.iterrows():
            avg_salary_value = row["avg_salary"]
            # pandas representa la ausencia de datos como NaN, que no es serializable ni almacenable como None directamente en SQL
            if pd.isna(avg_salary_value):
                avg_salary_value = None
            else:
                avg_salary_value = float(avg_salary_value)

            skill_id = int(row["skill_id"])
            city_id = int(row["city_id"])
            nuevo_demand_count = int(row["demand_count"])

            target_date = today - timedelta(days=7)
            prev_snapshot = TrendSnapshotRepository.get_by_skill_city_date(skill_id, city_id, target_date)

            if not prev_snapshot or not prev_snapshot.demand_count:
                growth_rate = None
            else:
                previo_demand_count = prev_snapshot.demand_count
                growth_rate = round(((nuevo_demand_count - previo_demand_count) / previo_demand_count) * 100, 2)
                growth_rate = max(min(growth_rate, 999.99), -999.99)

            snapshot_data = {
                "skill_id": skill_id,
                "city_id": city_id,
                "date": today,
                "demand_count": nuevo_demand_count,
                "avg_salary": avg_salary_value,
                "growth_rate": growth_rate,
            }

            result = TrendSnapshotRepository.upsert(snapshot_data)
            if result:
                snapshots_created += 1

        return snapshots_created
