# Registramos aquí todas las rutas de gestión de alertas:
# crear, listar, actualizar y eliminar alertas del usuario autenticado
from flask import Blueprint

alerts_bp = Blueprint("alerts", __name__)
