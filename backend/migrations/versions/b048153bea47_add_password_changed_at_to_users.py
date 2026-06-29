"""add password_changed_at to users

Revision ID: b048153bea47
Revises: 3e1b8af1978c
Create Date: 2026-06-25 22:49:16.739540

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b048153bea47'
down_revision = '3e1b8af1978c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'password_changed_at',
                sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
            )
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('password_changed_at')
