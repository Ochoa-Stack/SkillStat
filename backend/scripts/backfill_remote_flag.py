import os
import click
from dotenv import load_dotenv

# Asegurar que estamos en el directorio base correcto para cargar .env si es necesario
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

from app import create_app
from app.extensions import db
from app.models.job import Job
from app.services.ingestion_service import IngestionService

@click.command()
@click.option('--execute', is_flag=True, help="Ejecutar los cambios en la base de datos (por defecto es dry-run)")
def backfill_remote_flag(execute):
    """
    Recalcula el campo 'remote' de todos los jobs existentes usando la nueva lógica de IngestionService. Por defecto corre en modo dry-run (solo reporta). Usa --execute para aplicar los cambios. """
    app = create_app(os.getenv("FLASK_ENV", "development"))
    
    with app.app_context():
        print(f"Iniciando backfill de flag 'remote' (Modo: {'EXECUTE' if execute else 'DRY-RUN'})")
        print("-" * 60)
        
        jobs = db.session.execute(db.select(Job)).scalars().all()
        
        total_jobs = len(jobs)
        changed_to_true = 0
        changed_to_false = 0
        unchanged = 0
        errors = 0
        
        for job in jobs:
            try:
                # El título o descripción pueden ser None en la BD? Según los modelos y el schema, title y description suelen ser strings, pero por precaución:
                title = job.title or ""
                description = job.raw_description or ""
                
                new_remote = IngestionService._compute_is_remote(title, description)
                
                if new_remote != job.remote:
                    if new_remote is True:
                        changed_to_true += 1
                    else:
                        changed_to_false += 1
                        
                    if execute:
                        job.remote = new_remote
                        db.session.commit()
                        print(f"Actualizado Job ID {job.id}: remote -> {new_remote}")
                else:
                    unchanged += 1
            except Exception as e:
                errors += 1
                print(f"Error procesando Job ID {job.id}: {e}")
                if execute:
                    db.session.rollback()
                    
        print("-" * 60)
        print("Resumen del backfill:")
        print(f"  Total de jobs analizados : {total_jobs}")
        print(f"  Cambiaron a True         : {changed_to_true}")
        print(f"  Cambiaron a False        : {changed_to_false}")
        print(f"  Sin cambios              : {unchanged}")
        print(f"  Errores                  : {errors}")
        
        if not execute:
            print("\nNOTA: Ejecución en modo DRY-RUN. No se guardaron cambios en la base de datos.")
            print("      Para aplicar los cambios, ejecuta el script con el flag --execute.")

if __name__ == '__main__':
    backfill_remote_flag()
