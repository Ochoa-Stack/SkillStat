# Registramos aquí todas las rutas relacionadas con autenticación:
# registro de cuenta, inicio de sesión y cierre de sesión
from flask import Blueprint

auth_bp = Blueprint("auth", __name__)
