from app.repositories.alert_repository import AlertRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.repositories.user_repository import UserRepository
from app.repositories.skill_repository import SkillRepository
from app.clients.sendgrid_client import EmailClient
from app.utils.errors import AppError

class AlertsService:
    # Aísla la lógica de evaluación de notificaciones. Su diseño permite ser ejecutado de forma asíncrona (ej. Celery/APScheduler) sin bloquear la ingesta principal.

    @classmethod
    def evaluate_and_notify(cls) -> int:
        active_alerts = AlertRepository.get_all()
        if not active_alerts:
            return 0

        notifications_sent = 0

        for alert in active_alerts:
            # Evaluamos contra el snapshot más reciente para determinar si se superó el umbral
            latest_trend = TrendSnapshotRepository.get_latest_by_skill(alert.skill_id)
            
            if not latest_trend or latest_trend.demand_count < alert.threshold_value:
                continue

            user = UserRepository.get_by_id(alert.user_id)
            skill = SkillRepository.get_by_id(alert.skill_id)
            
            if not user or not skill:
                continue

            subject = f"Alerta SkillStat: {skill.name} ha superado tu umbral"
            html_content = f"""
            <h3>Alerta de Mercado Laboral</h3>
            <p>Hola, tu alerta configurada para <strong>{skill.name}</strong> ha sido activada.</p>
            <p>El mercado actual registra <strong>{latest_trend.demand_count}</strong> vacantes activas, superando tu umbral de {alert.threshold_value}.</p>
            <p><a href="https://skillstat.mx/panorama">Ver en el Panorama</a></p>
            """

            try:
                # Delegamos el envío al cliente Wrapper. 
                # Atrapamos errores para evitar que el fallo de un email cancele el ciclo entero.
                success = EmailClient.send_alert_email(user.email, subject, html_content)
                if success:
                    notifications_sent += 1
            except AppError:
                continue

        return notifications_sent
