from flask_jwt_extended import create_access_token

def generate_tokens(user_id: int, role: str) -> dict:
    # Inyectamos el rol directamente en los claims del token JWT para evitar consultas redundantes a la base de datos en las rutas protegidas (ahorro de latencia). No pasamos expires_delta aqui; dejamos que JWT_ACCESS_TOKEN_EXPIRES en config.py sea el único punto de referencia sobre cuanto dura la sesion.
    access_token = create_access_token(
        identity=str(user_id),
        additional_claims={"role": role},
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
    }
