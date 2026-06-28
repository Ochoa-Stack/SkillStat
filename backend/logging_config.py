import logging
import sys
from logging.handlers import RotatingFileHandler

# Log a archivo para que el checkpoint pueda leer los tokens de reset en modo desarrollo sin depender de que el stderr de Flask llegue al terminal de PowerShell (que lo redirige de forma inconsistente).
handler = RotatingFileHandler("flask_dev.log", maxBytes=1_000_000, backupCount=1, encoding="utf-8")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
handler.setFormatter(formatter)

# Adjuntamos al root logger para capturar logger.info() de cualquier módulo
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.DEBUG)

# También a stderr para no perder visibilidad en la consola
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logging.getLogger().addHandler(stream_handler)
