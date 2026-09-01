"""fix: sync categories_id_seq after seed without setval

Revision ID: a1b2c3d4e5f6
Revises: 9a104cdbdaed
Create Date: 2026-07-27 00:00:00.000000

La migración 401c30988716 sembró las categorías base (ids 1-6) con ids
explícitos usando ON CONFLICT DO NOTHING, pero omitió el ajuste de la
secuencia categories_id_seq. Esto hace que la primera inserción orgánica
de una Category (p.ej. en tests de integración) intente reutilizar el
id=1 ya ocupado, produciendo:

    duplicate key value violates unique constraint "categories_pkey"

Este patrón es idéntico al que afectó a cities y se corrigió en
9a104cdbdaed. Se aplica la misma solución: SELECT setval() con
GREATEST(MAX(id)+1, 7) para que la secuencia arranque por encima del
id más alto ya sembrado (id=6), sin depender de la condición de la tabla.

La operación es idempotente: si la secuencia ya fue avanzada (p.ej. en
un entorno que ya tenía inserciones orgánicas de categories), GREATEST
garantiza que no la retrocedemos.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9a104cdbdaed'
branch_labels = None
depends_on = None


def upgrade():
    # Adelantar la secuencia por encima del id máximo ya sembrado (6),
    # para que el próximo INSERT orgánico comience desde id=7 como mínimo.
    # GREATEST(MAX(id)+1, 7) es defensivo: si ya existen filas con id > 6,
    # usamos ese valor; si la tabla solo tiene las filas sembradas (max=6),
    # partimos de 7.
    op.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('categories', 'id'),
                GREATEST((SELECT MAX(id) + 1 FROM categories), 7)
            )
            """
        )
    )


def downgrade():
    # No hay reversión significativa posible para un ajuste de secuencia:
    # retroceder la secuencia podría causar colisiones con filas ya
    # insertadas en producción. Se documenta explícitamente como decisión
    # de diseño, no como omisión.
    pass
