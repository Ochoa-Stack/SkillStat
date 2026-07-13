from marshmallow import Schema, fields, validate


class UserRoleSchema(Schema):
    role = fields.String(
        required=True,
        validate=validate.OneOf(
            ["REGISTERED", "ADMIN"],
            error="El rol debe ser REGISTERED o ADMIN.",
        ),
        error_messages={"required": "El campo role es obligatorio."},
    )


class UserStatusSchema(Schema):
    is_active = fields.Boolean(
        required=True,
        error_messages={"required": "El campo is_active es obligatorio."},
    )
