import os
import click
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    # La bandera de depuración se deriva estrictamente del entorno para prevenir la exposición de trazas de ejecución en entornos de producción
    debug_mode = os.getenv("FLASK_ENV") == "development"
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)


@app.cli.command("ingest-jobs")
@click.option("--pages", default=1, show_default=True, help="Número de páginas de Adzuna a consumir (50 vacantes por página).")
@click.option("--what", default="software developer", show_default=True, help="Término de búsqueda enviado a Adzuna.")
@click.option("--country", default="mx", show_default=True, help="Código de país ISO para la búsqueda en Adzuna.")
def ingest_jobs(pages, what, country):
    """Dispara la ingesta completa de vacantes desde Adzuna con geocodificación via Nominatim"""
    import sys
    # Forzar UTF-8 en Windows para evitar UnicodeEncodeError con cp1252 al imprimir acentos o emojis
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    from app.services.ingestion_service import IngestionService

    click.echo(f"Iniciando ingesta: country={country}, what='{what}', pages={pages}")
    click.echo("-" * 60)

    stats = IngestionService.run_ingestion(country=country, what=what, pages=pages, verbose=True)

    click.echo("-" * 60)
    click.echo("Resumen de ingesta:")
    click.echo(f"  Vacantes recibidas de Adzuna : {stats['fetched']}")
    click.echo(f"  Vacantes guardadas           : {stats['processed']}")
    click.echo(f"  Duplicados (hash repetido)   : {stats['duplicates']}")
    click.echo(f"  Errores reales               : {stats['errors']}")
    click.echo(f"  Ciudades nuevas insertadas   : {stats['cities_created']}")
    click.echo(f"  Fallback a Mexico Nacional   : {stats['fallback']}")


@app.cli.command("generate-snapshots")
def generate_snapshots_cmd():
    """Recalcula los TrendSnapshots analíticos a partir de los JobSkills clasificados. Debe ejecutarse después de clasificar las vacantes ingeridas"""
    import sys
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    from app.services.market_trends_service import MarketTrendsService

    count = MarketTrendsService.generate_snapshots()
    click.echo(f"Snapshots generados: {count}")