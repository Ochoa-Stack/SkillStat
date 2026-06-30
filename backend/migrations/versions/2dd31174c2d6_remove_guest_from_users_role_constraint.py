"""remove GUEST from users role constraint

Revision ID: 2dd31174c2d6
Revises: b048153bea47
Create Date: 2026-06-28 22:38:18.200252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2dd31174c2d6'
down_revision = 'b048153bea47'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('chk_users_role', 'users', type_='check')
    op.create_check_constraint('chk_users_role', 'users', "role IN ('REGISTERED', 'ADMIN')")


def downgrade():
    op.drop_constraint('chk_users_role', 'users', type_='check')
    op.create_check_constraint('chk_users_role', 'users', "role IN ('GUEST', 'REGISTERED', 'ADMIN')")
