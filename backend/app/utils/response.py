from typing import Any, Dict, Tuple
from flask import jsonify, Response

def success_response(data: Any = None, meta: Dict = None, status_code: int = 200) -> Tuple[Response, int]:
    # Estructuramos una respuesta predecible para que el frontend no tenga que
    # adivinar en qué llave viene la información tras cada petición.
    response_body = {}
    if data is not None:
        response_body["data"] = data
    if meta is not None:
        response_body["meta"] = meta
    return jsonify(response_body), status_code

def error_response(code: str, message: str, status_code: int = 400) -> Tuple[Response, int]:
    # Aislamos el formato de error para garantizar que todas las fallas del sistema
    # sean procesadas uniformemente por el interceptor global de Axios en el frontend.
    return jsonify({
        "error": {
            "code": code,
            "message": message
        }
    }), status_code
