"""enable unaccent extension and add functional index on cities name

Revision ID: e89b2bf6614f
Revises: e269761308d8
Create Date: 2026-07-31 17:18:00.737000

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


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
    