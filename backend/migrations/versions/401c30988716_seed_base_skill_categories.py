"""seed base skill categories

Revision ID: 401c30988716
Revises: ce332628ddba
Create Date: 2026-07-18 11:06:08.837470

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '401c30988716'
down_revision = 'ce332628ddba'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO categories (id, name) VALUES
        (1, 'General'),
        (2, 'Frontend'),
        (3, 'Backend'),
        (4, 'DevOps y Cloud'),
        (5, 'Datos e IA'),
        (6, 'Arquitectura')
        ON CONFLICT (id) DO NOTHING;
    """)

def downgrade():
    # Solo eliminamos si no tienen skills vinculados, para no borrar
    # categorias con datos reales ya clasificados en un entorno donde
    # si se uso esta migracion para crearlas desde cero.
    op.execute("""
        DELETE FROM categories
        WHERE id IN (1, 2, 3, 4, 5, 6)
        AND id NOT IN (SELECT DISTINCT category_id FROM skills WHERE category_id IS NOT NULL);
    """)
