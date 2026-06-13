from marshmallow import Schema, fields

class SkillResponseSchema(Schema):
    # El catálogo de habilidades es de solo lectura para el cliente.
    # Este esquema asegura que el dropdown del frontend reciba exactamente los tipos de datos esperados y no exponga metadata interna.
    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    canonical_name = fields.String(dump_only=True)
