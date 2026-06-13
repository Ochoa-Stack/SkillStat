from marshmallow import Schema, fields, validate

class AlertRequestSchema(Schema):
    # Validamos estrictamente que el threshold sea un número positivo.
    # Evitamos que un usuario malintencionado o un error de UI envíe valores negativos que corrompan la lógica de evaluación en el servicio.
    skill_id = fields.Integer(required=True, strict=True, error_messages={"required": "El ID de la habilidad es obligatorio.", "invalid": "El ID debe ser un número entero."})
    threshold_value = fields.Integer(
        required=True, 
        strict=True, 
        validate=validate.Range(min=1), 
        error_messages={
            "required": "El umbral es obligatorio.", 
            "validator_failed": "El umbral debe ser mayor a 0.",
            "invalid": "El umbral debe ser un número entero."
        }
    )

class AlertResponseSchema(Schema):
    # Exponemos la estructura de la alerta al frontend.
    id = fields.Integer(dump_only=True)
    skill_id = fields.Integer(dump_only=True)
    threshold_value = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
