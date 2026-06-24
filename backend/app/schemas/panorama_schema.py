from marshmallow import Schema, fields


class SkillTrendSchema(Schema):
    # Representa una habilidad con su metrica de demanda actual. Usado en skills/top y como bloque base de otros endpoints.
    skill_id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    demand_count = fields.Integer(dump_only=True)
    growth_rate = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    avg_salary = fields.Decimal(dump_only=True, allow_none=True, as_string=True)


class SummaryResponseSchema(Schema):
    # KPIs globales del Panorama: totales y tendencias destacadas.
    total_jobs = fields.Integer(dump_only=True)
    total_skills_tracked = fields.Integer(dump_only=True)
    total_companies = fields.Integer(dump_only=True)
    top_emerging_skill = fields.Nested(SkillTrendSchema, dump_only=True, allow_none=True)
    top_declining_skill = fields.Nested(SkillTrendSchema, dump_only=True, allow_none=True)
    last_updated = fields.Date(dump_only=True, allow_none=True)


class CityOptionSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)


class SkillOptionSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)


class CatalogsResponseSchema(Schema):
    # Listas livianas para alimentar selectores del frontend.
    skills = fields.List(fields.Nested(SkillOptionSchema), dump_only=True)
    cities = fields.List(fields.Nested(CityOptionSchema), dump_only=True)


class TrendPointSchema(Schema):
    # Un punto en la serie temporal de una habilidad especifica.
    date = fields.Date(dump_only=True)
    demand_count = fields.Integer(dump_only=True)


class TrendsResponseSchema(Schema):
    skill_id = fields.Integer(dump_only=True)
    skill_name = fields.String(dump_only=True)
    series = fields.List(fields.Nested(TrendPointSchema), dump_only=True)


class GeoDistributionSchema(Schema):
    # Demanda de una habilidad agrupada por ciudad.
    city_id = fields.Integer(dump_only=True)
    city_name = fields.String(dump_only=True)
    demand_count = fields.Integer(dump_only=True)


class GeoResponseSchema(Schema):
    skill_id = fields.Integer(dump_only=True, allow_none=True)
    skill_name = fields.String(dump_only=True, allow_none=True)
    distribution = fields.List(fields.Nested(GeoDistributionSchema), dump_only=True)


class SalaryResponseSchema(Schema):
    # Cruce de habilidad contra rango salarial promedio.
    skill_id = fields.Integer(dump_only=True)
    skill_name = fields.String(dump_only=True)
    avg_salary_min = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    avg_salary_max = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    sample_size = fields.Integer(dump_only=True)


class CompareSkillBlockSchema(Schema):
    # Bloque de metricas para una sola habilidad dentro de la comparacion.
    skill_id = fields.Integer(dump_only=True)
    skill_name = fields.String(dump_only=True)
    demand_count = fields.Integer(dump_only=True)
    avg_salary = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    series = fields.List(fields.Nested(TrendPointSchema), dump_only=True)


class CompareResponseSchema(Schema):
    skills = fields.List(fields.Nested(CompareSkillBlockSchema), dump_only=True)
