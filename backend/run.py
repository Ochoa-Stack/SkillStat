import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    # La bandera de depuración se deriva estrictamente del entorno para prevenir la exposición de trazas de ejecución en entornos de producción.
    debug_mode = os.getenv("FLASK_ENV") == "development"
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)