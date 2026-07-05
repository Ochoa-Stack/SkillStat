"""harden users created_at not null constraint

Revision ID: 6d85e79a3808
Revises: 5fc89dde67bf
Create Date: 2026-07-04 15:32:14.004434

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d85e79a3808'
down_revision = '5fc89dde67bf'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE users SET created_at = now() WHERE created_at IS NULL")
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('created_at',
            existing_type=sa.DateTime(),
            nullable=False,
            server_default=sa.text('now()'))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('created_at',
            existing_type=sa.DateTime(),
            nullable=True,
            server_default=None)
