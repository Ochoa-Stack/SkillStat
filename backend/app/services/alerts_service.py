import logging
from app.repositories.alert_repository import AlertRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository
from app.repositories.user_repository import UserRepository
from app.repositories.skill_repository import SkillRepository
from app.services.email_service import send_alert_email
from app.utils.errors import AppError

logger = logging.getLogger(__name__)

class AlertsService:
    @classmethod
    def _build_notification_content(cls, alert, skill, latest_trend):
        if alert.alert_type == "ABSOLUTE":
            subject = f"Alerta SkillStat: {skill.name} ha superado tu umbral"
            html_content = f"""
            <h3>Alerta de Mercado Laboral</h3>
            <p>Hola, tu alerta configurada para <strong>{skill.name}</strong> ha sido activada.</p>
            <p>El mercado actual registra <strong>{latest_trend.demand_count}</strong> vacantes activas, superando tu umbral de {alert.threshold_value}.</p>
            <p><a href="https://skillstat-ss.onrender.com/views/panorama.html">Ver en el Panorama</a></p>
            """
        else:
            subject = f"Alerta SkillStat: {skill.name} está en tendencia de crecimiento"
            html_content = f"""
            <h3>Alerta de Mercado Laboral</h3>
            <p>Hola, tu alerta de tendencia configurada para <strong>{skill.name}</strong> ha sido activada.</p>
            <p>Esta habilidad ha crecido <strong>{latest_trend.growth_rate}%</strong> en la última semana, superando tu umbral de {alert.threshold_percentage}%.</p>
            <p><a href="https://skillstat-ss.onrender.com/views/panorama.html">Ver en el Panorama</a></p>
            """
        return subject, html_content

    @classmethod
    def evaluate_and_notify(cls) -> int:
        active_alerts = AlertRepository.get_active()
        if not active_alerts:
            return 0
        notifications_sent = 0
        for alert in active_alerts:
            latest_trend = TrendSnapshotRepository.get_latest_by_skill(alert.skill_id)
            if not latest_trend:
                continue
            triggered = False
            if alert.alert_type == "ABSOLUTE":
                if latest_trend.demand_count is not None and latest_trend.demand_count >= alert.threshold_value:
                    triggered = True
            elif alert.alert_type == "TREND":
                # Sin historial de 7 dias, growth_rate es None, no evaluamos, no notificamos. Ausencia de dato no es lo mismo que "no se cumplio".
                if latest_trend.growth_rate is not None and latest_trend.growth_rate >= alert.threshold_percentage:
                    triggered = True
            if not triggered:
                continue
            user = UserRepository.get_by_id(alert.user_id)
            skill = SkillRepository.get_by_id(alert.skill_id)
            if not user or not skill:
                continue
            
            subject, html_content = cls._build_notification_content(alert, skill, latest_trend)
            
            try:
                send_alert_email(user.email, subject, html_content)
                notifications_sent += 1
            except AppError as e:
                logger.warning(
                    "Fallo al enviar correo de alerta: alert_id=%s user_id=%s. Error: %s",
                    alert.id, alert.user_id, str(e)
                )
                continue
        return notifications_sent
