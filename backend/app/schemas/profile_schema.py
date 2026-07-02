from marshmallow import Schema, fields, validate, validates_schema, ValidationError

from app.schemas.auth_schema import validate_password_strength


class UpdateProfileSchema(Schema):
    first_name = fields.String(
        load_default=None,
        validate=validate.Length(min=1, max=50),
    )
    last_name = fields.String(
        load_default=None,
        validate=validate.Length(min=1, max=50),
    )
    intent = fields.String(
        load_default=None,
        validate=validate.OneOf(
            ["ESTUDIANTE", "RECLUTADOR"],
            error="El intent debe ser ESTUDIANTE o RECLUTADOR.",
        ),
        allow_none=True,
    )

    @validates_schema
    def require_at_least_one_field(self, data, **kwargs):
        # Un PATCH sin ningun campo modificado no tiene sentido funcional, lo rechazamos con un mensaje claro.
        if not any(v is not None for v in data.values()):
            raise ValidationError("Se requiere al menos un campo para actualizar el perfil.")


class AddSkillSchema(Schema):
    skill_id = fields.Integer(
        required=True,
        strict=True,
        error_messages={"required": "El skill_id es obligatorio."},
    )


class ChangePasswordSchema(Schema):
    current_password = fields.String(
        required=True,
        error_messages={"required": "La contrasena actual es obligatoria."},
    )
    # Reutilizamos el validador de complejidad importandolo directamente desde auth_schema, no duplicando la logica, para que cualquier cambio futuro a las reglas aplique en ambos flujos.
    new_password = fields.String(
        required=True,
        validate=[validate.Length(min=8, max=128), validate_password_strength],
        error_messages={"required": "La nueva contrasena es obligatoria."},
    )
