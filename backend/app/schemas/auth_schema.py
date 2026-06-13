from marshmallow import Schema, fields, validate, pre_load

class UserRegistrationSchema(Schema):
    # Alineación estricta con el modelo SQLAlchemy (first_name, last_name)
    email = fields.Email(required=True, error_messages={"required": "El correo es obligatorio.", "invalid": "Formato de correo inválido."})
    password = fields.String(required=True, validate=validate.Length(min=8, max=128), error_messages={"required": "La contraseña es obligatoria."})
    first_name = fields.String(required=True, validate=validate.Length(min=2, max=50), error_messages={"required": "El nombre es obligatorio."})
    last_name = fields.String(required=True, validate=validate.Length(min=2, max=50), error_messages={"required": "El apellido es obligatorio."})

    @pre_load
    def format_input(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower().strip()
        return data

class UserLoginSchema(Schema):
    email = fields.Email(required=True, error_messages={"required": "El correo es obligatorio.", "invalid": "Formato de correo inválido."})
    password = fields.String(required=True, error_messages={"required": "La contraseña es obligatoria."})

class UserResponseSchema(Schema):
    # Exponemos la estructura desagregada del nombre y mantenemos la censura de la contraseña
    id = fields.Integer(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.String(dump_only=True)
    last_name = fields.String(dump_only=True)
    role = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
