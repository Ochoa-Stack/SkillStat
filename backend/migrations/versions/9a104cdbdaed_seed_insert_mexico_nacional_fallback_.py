"""seed: insert Mexico Nacional fallback city (id=1)

Revision ID: 9a104cdbdaed
Revises: beb2d2367ab1
Create Date: 2026-07-25 14:54:35.785950

Garantiza que la fila id=1 ("México Nacional") exista antes de cualquier
ingesta. IngestionService asume que MEXICO_NACIONAL_CITY_ID=1 siempre
está disponible; sin esta semilla la primera ciudad orgánica toma ese id
por autoincremento, corrompiendo silenciosamente las vacantes sin
geocodificación.

La sentencia ON CONFLICT DO NOTHING hace la migración idempotente: segura
de re-ejecutar si por alguna razón ya existiera la fila (p.ej., si se
corre flask db upgrade dos veces o si la migración se aplica en un
entorno que ya tenía la fila de forma manual).

El SELECT setval(...) al final adelanta la secuencia por encima del id=1
para que la próxima inserción orgánica comience desde id=2 y no intente
reusar ni colisionar con el id reservado. Usamos SELECT GREATEST(2,
MAX(id)+1) para que sea seguro incluso si ya hubiera filas con ids > 1.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a104cdbdaed'
down_revision = 'beb2d2367ab1'
branch_labels = None
depends_on = None


def upgrade():
    # Insertar la fila semilla con id=1 explícito.
    # state, lat, lon son nullable → NULL es el valor correcto para un
    # fallback genérico que no representa una ciudad geocodificada real.
    # ON CONFLICT (id) DO NOTHING garantiza idempotencia.
    op.execute(
        sa.text(
            """
            INSERT INTO cities (id, name, state, country, lat, lon)
            VALUES (1, 'México Nacional', NULL, 'MX', NULL, NULL)
            ON CONFLICT (id) DO NOTHING
            """
        )
    )

    # Adelantar la secuencia para que la siguiente inserción orgánica
    # no intente asignarse el id=1 ya reservado.
    # GREATEST(2, MAX(id)+1) es defensivo: cubre el caso en que ya
    # hubiera filas con id > 1 antes de correr esta migración.
    op.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('cities', 'id'),
                GREATEST(2, (SELECT MAX(id) + 1 FROM cities))
            )
            """
        )
    )


def downgrade():
    # Eliminar únicamente la fila semilla. Usamos la combinación
    # id=1 AND name='México Nacional' para no borrar accidentalmente
    # una fila distinta si el contexto cambia.
    op.execute(
        sa.text(
            "DELETE FROM cities WHERE id = 1 AND name = 'México Nacional'"
        )
    )
