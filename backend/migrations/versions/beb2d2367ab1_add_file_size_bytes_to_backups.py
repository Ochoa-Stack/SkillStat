"""add_file_size_bytes_to_backups

Revision ID: beb2d2367ab1
Revises: 401c30988716
Create Date: 2026-07-19 08:51:27.262260

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'beb2d2367ab1'
down_revision = '401c30988716'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('backups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_size_bytes', sa.BigInteger(), nullable=True))


def downgrade():
    with op.batch_alter_table('backups', schema=None) as batch_op:
        batch_op.drop_column('file_size_bytes')
