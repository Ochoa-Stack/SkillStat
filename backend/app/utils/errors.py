class AppError(Exception):
    # Excepción base para que la capa de Controladores pueda atrapar cualquier
    # fallo lógico de la capa de Servicios sin acoplarse a librerías HTTP.
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

class ResourceNotFoundError(AppError):
    def __init__(self, message: str = "El recurso solicitado no fue encontrado."):
        super().__init__(message, code="NOT_FOUND", status_code=404)

class ValidationError(AppError):
    def __init__(self, message: str = "Error de validación de datos."):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)

class UnauthorizedError(AppError):
    def __init__(self, message: str = "No autorizado para realizar esta acción."):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)

class ConflictError(AppError):
    def __init__(self, message: str = "Conflicto con el estado actual del recurso."):
        super().__init__(message, code="CONFLICT", status_code=409)
