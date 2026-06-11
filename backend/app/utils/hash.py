import bcrypt

def hash_password(password: str) -> str:
    # Usamos bcrypt con gensalt() para proteger contra ataques de rainbow tables
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # La comparación siempre debe hacerse a nivel de bytes para evitar brechas de codificación
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
