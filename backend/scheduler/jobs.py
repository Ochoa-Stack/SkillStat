from app.services.market_trends_service import MarketTrendsService
from app.services.alerts_service import AlertsService


def daily_pipeline(app):
    # Recibimos la instancia concreta de app en lugar de usar el proxy current_app porque APScheduler ejecuta este job en un hilo separado donde el proxy no tiene contexto activo garantizado.
    with app.app_context():
        MarketTrendsService.generate_snapshots()
        AlertsService.evaluate_and_notify()