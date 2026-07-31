"""enable unaccent extension and add functional index on cities name

Revision ID: e89b2bf6614f
Revises: e269761308d8
Create Date: 2026-07-31 17:18:04.748824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e89b2bf6614f'
down_revision = 'e269761308d8'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    op.execute(
        "CREATE OR REPLACE FUNCTION immutable_unaccent(text) "
        "RETURNS text AS $$ SELECT unaccent('unaccent', $1) $$ "
        "LANGUAGE sql IMMUTABLE;"
    )
    op.execute(
        "CREATE INDEX ix_cities_name_unaccent ON cities "
        "(immutable_unaccent(lower(name)));"
    )

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_cities_name_unaccent;")
    op.execute("DROP FUNCTION IF EXISTS immutable_unaccent(text);")
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
