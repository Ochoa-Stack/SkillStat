# Registramos aquí todas las rutas de administración del sistema:
# gestión de usuarios, ejecución de respaldos y restauración de datos
from flask import Blueprint

admin_bp = Blueprint("admin", __name__)
