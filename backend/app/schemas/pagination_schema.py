from marshmallow import Schema, fields


class PaginationMetaSchema(Schema):
    # Schema reutilizable para envolver cualquier respuesta paginada del API. 'total_pages' se calcula en el controller para evitar duplicar la lógica de división en cada serialización.
    total = fields.Integer(dump_only=True)
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
