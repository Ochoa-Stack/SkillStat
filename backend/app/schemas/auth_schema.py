import re
from marshmallow import Schema, fields, validate, pre_load, ValidationError


def validate_password_strength(password):
    # Aplicamos longitud minima ya la valida validate.Length por separado, aqui solo checamos composicion.
    if not re.search(r"[A-Z]", password):
        raise ValidationError("La contraseña debe incluir al menos una mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("La contraseña debe incluir al menos una minúscula.")
    if not re.search(r"\d", password):
        raise ValidationError("La contraseña debe incluir al menos un número.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValidationError("La contraseña debe incluir al menos un carácter especial.")

class UserRegistrationSchema(Schema):
    # Alineación estricta con el modelo SQLAlchemy (first_name, last_name)
    email = fields.Email(required=True, error_messages={"required": "El correo es obligatorio.", "invalid": "Formato de correo inválido."})
    password = fields.String(
        required=True,
        validate=[validate.Length(min=8, max=128), validate_password_strength],
        error_messages={"required": "La contraseña es obligatoria."},
    )
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
    id = fields.Integer(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.String(dump_only=True)
    last_name = fields.String(dump_only=True)
    role = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class ForgotPasswordSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages={
            "required": "El correo es obligatorio.",
            "invalid": "Formato de correo inválido.",
        },
    )

    @pre_load
    def normalize_email(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower().strip()
        return data


class EmailOnlySchema(Schema):
    """Schema mínimo para endpoints que sólo necesitan un correo electrónico.
    Independiente de ForgotPasswordSchema para evitar acoplamiento conceptual entre flujos distintos (resend-verification vs. forgot-password)"""

    email = fields.Email(
        required=True,
        error_messages={
            "required": "El correo es obligatorio.",
            "invalid": "Formato de correo inválido.",
        },
    )

    @pre_load
    def normalize_email(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower().strip()
        return data


class ResetPasswordSchema(Schema):
    token = fields.String(
        required=True,
        error_messages={"required": "El token es obligatorio."},
    )
    # Reutilizamos el mismo validador de complejidad definido arriba en este mismo archivo, la regla vive en un solo lugar, no copiada.
    new_password = fields.String(
        required=True,
        validate=[validate.Length(min=8, max=128), validate_password_strength],
        error_messages={"required": "La nueva contraseña es obligatoria."},
    )
