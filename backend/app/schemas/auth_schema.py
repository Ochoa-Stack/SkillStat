from marshmallow import Schema, fields, validate, pre_load

class UserRegistrationSchema(Schema):
    # Establecemos restricciones estrictas de longitud y formato desde el borde del sistema para rechazar ataques de inyección o payloads masivos antes de que consuman ciclos de procesamiento o interactúen con la BD.
    email = fields.Email(required=True, error_messages={"required": "El correo es obligatorio.", "invalid": "Formato de correo inválido."})
    password = fields.String(required=True, validate=validate.Length(min=8, max=128), error_messages={"required": "La contraseña es obligatoria."})
    name = fields.String(required=True, validate=validate.Length(min=2, max=100), error_messages={"required": "El nombre es obligatorio."})

    @pre_load
    def format_input(self, data, **kwargs):
        # Normalizamos el correo a minúsculas para evitar colisiones de unicidad en PostgreSQL provocadas por capitalización inconsistente del usuario.
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower().strip()
        return data

class UserLoginSchema(Schema):
    # Para el login solo requerimos presencia, no validamos longitud de contraseña aquí para no dar pistas a posibles atacantes sobre nuestras políticas internas.
    email = fields.Email(required=True, error_messages={"required": "El correo es obligatorio.", "invalid": "Formato de correo inválido."})
    password = fields.String(required=True, error_messages={"required": "La contraseña es obligatoria."})

class UserResponseSchema(Schema):
    # Plantilla de serialización de salida. Omitimos explícitamente el campo 'password' en la definición para garantizar que el hash criptográfico jamás se filtre al frontend.
    id = fields.Integer(dump_only=True)
    email = fields.Email(dump_only=True)
    name = fields.String(dump_only=True)
    role = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
