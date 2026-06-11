from datetime import timedelta
from flask_jwt_extended import create_access_token

def generate_tokens(user_id: int, role: str) -> dict:
    # Inyectamos el rol directamente en los claims del token JWT para evitar 
    # consultas redundantes a la base de datos en las rutas protegidas (ahorro de latencia)
    access_token = create_access_token(
        identity=str(user_id),
        additional_claims={"role": role},
        expires_delta=timedelta(hours=2)
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 7200
    }
