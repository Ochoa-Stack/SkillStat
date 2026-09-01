"""add user_skills table

Revision ID: 83e1f6043b93
Revises: 2dd31174c2d6
Create Date: 2026-06-28 22:38:28.349877

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83e1f6043b93'
down_revision = '2dd31174c2d6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user_skills',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('skill_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'skill_id')
    )


def downgrade():
    op.drop_table('user_skills')
