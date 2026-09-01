"""rename user_alerts.threshold to threshold_value

Revision ID: 146283b709e9
Revises: 6d85e79a3808
Create Date: 2026-07-08 19:07:02.019892

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '146283b709e9'
down_revision = '6d85e79a3808'
branch_labels = None
depends_on = None


def upgrade():
    # Renombramos la columna en vez de drop+add para que la operación sea atómica
    # y no destruya datos si la tabla no estuviera vacía
    op.alter_column('user_alerts', 'threshold', new_column_name='threshold_value')


def downgrade():
    op.alter_column('user_alerts', 'threshold_value', new_column_name='threshold')
