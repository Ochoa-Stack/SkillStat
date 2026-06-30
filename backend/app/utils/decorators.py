from functools import wraps
from flask_jwt_extended import get_jwt_identity
from app.utils.response import error_response


def role_required(*allowed_roles):
    """Decorador de autorización por rol para rutas de la API.
    Debe aplicarse siempre después de @jwt_required() en el orden de decoradores, es decir, @jwt_required() va encima y @role_required(...) va debajo. Esto es necesario porque jwt_required debe ejecutarse primero: sin él no existe identidad verificada que este decorador pueda consultar.

    Uso:
        @jwt_required()
        @role_required('ADMIN')
        def mi_ruta():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Importación diferida para evitar ciclo con db en el arranque de la app.
            from app.repositories.user_repository import UserRepository

            user_id = get_jwt_identity()
            user = UserRepository.get_by_id(int(user_id)) if user_id else None

            if not user or user.role not in allowed_roles:
                return error_response(
                    code="FORBIDDEN",
                    message="No tienes permiso para acceder a este recurso.",
                    status_code=403,
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator
