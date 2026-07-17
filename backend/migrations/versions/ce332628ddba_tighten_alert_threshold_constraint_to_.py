"""tighten alert threshold constraint to exclude cross-type values

Revision ID: ce332628ddba
Revises: 33f2045987f9
Create Date: 2026-07-17 16:44:51.356054

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ce332628ddba'
down_revision = '33f2045987f9'
branch_labels = None
depends_on = None


def upgrade():
    # Reemplazamos el constraint existente por una version mas estricta que
    # exige explicitamente que el campo del OTRO tipo sea NULL, previniendo
    # que una fila tenga ambos campos poblados simultaneamente (DT-17).
    op.drop_constraint(
        'chk_alerts_threshold_matches_type',
        'user_alerts',
        type_='check',
    )
    op.create_check_constraint(
        'chk_alerts_threshold_matches_type',
        'user_alerts',
        "(alert_type = 'ABSOLUTE' AND threshold_value IS NOT NULL AND threshold_percentage IS NULL) OR "
        "(alert_type = 'TREND' AND threshold_percentage IS NOT NULL AND threshold_value IS NULL)",
    )


def downgrade():
    # Restaura la version anterior del constraint (sin la restriccion de NULL cruzado).
    op.drop_constraint(
        'chk_alerts_threshold_matches_type',
        'user_alerts',
        type_='check',
    )
    op.create_check_constraint(
        'chk_alerts_threshold_matches_type',
        'user_alerts',
        "(alert_type = 'ABSOLUTE' AND threshold_value IS NOT NULL) OR "
        "(alert_type = 'TREND' AND threshold_percentage IS NOT NULL)",
    )
