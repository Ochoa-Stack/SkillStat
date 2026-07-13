from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class AlertRequestSchema(Schema):
    skill_id = fields.Integer(
        required=True, strict=True,
        error_messages={"required": "El ID de la habilidad es obligatorio.", "invalid": "El ID debe ser un número entero."}
    )
    alert_type = fields.String(
        required=True,
        validate=validate.OneOf(["ABSOLUTE", "TREND"], error="alert_type debe ser ABSOLUTE o TREND."),
        error_messages={"required": "El tipo de alerta es obligatorio."}
    )
    threshold_value = fields.Integer(
        required=False, strict=True, allow_none=True,
        validate=validate.Range(min=1),
        error_messages={"validator_failed": "El umbral debe ser mayor a 0.", "invalid": "El umbral debe ser un número entero."}
    )
    threshold_percentage = fields.Decimal(
        required=False, allow_none=True, as_string=False,
        validate=validate.Range(min=0.01),
        error_messages={"validator_failed": "El porcentaje debe ser mayor a 0."}
    )

    @validates_schema
    def validate_threshold_matches_type(self, data, **kwargs):
        alert_type = data.get("alert_type")
        has_value = data.get("threshold_value") is not None
        has_percentage = data.get("threshold_percentage") is not None
        if alert_type == "ABSOLUTE":
            if not has_value:
                raise ValidationError("threshold_value es obligatorio para alertas de tipo ABSOLUTE.", field_name="threshold_value")
            if has_percentage:
                raise ValidationError("threshold_percentage no debe enviarse para alertas de tipo ABSOLUTE.", field_name="threshold_percentage")
        elif alert_type == "TREND":
            if not has_percentage:
                raise ValidationError("threshold_percentage es obligatorio para alertas de tipo TREND.", field_name="threshold_percentage")
            if has_value:
                raise ValidationError("threshold_value no debe enviarse para alertas de tipo TREND.", field_name="threshold_value")


class AlertResponseSchema(Schema):
    # Exponemos la estructura completa de la alerta al frontend, incluyendo tipo y umbrales por variante.
    id = fields.Integer(dump_only=True)
    skill_id = fields.Integer(dump_only=True)
    alert_type = fields.String(dump_only=True)
    threshold_value = fields.Integer(dump_only=True, allow_none=True)
    threshold_percentage = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    created_at = fields.DateTime(dump_only=True)
