"""add term and year to marks

Revision ID: e5fc0c65f5ef
Revises: 1af2e52f9a98
Create Date: 2026-07-19 21:27:11.742907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5fc0c65f5ef'
down_revision = '1af2e52f9a98'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('marks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('term', sa.String(length=10), nullable=False, server_default='Term 1'))
        batch_op.add_column(sa.Column('year', sa.Integer(), nullable=False, server_default='2026'))


def downgrade():
    with op.batch_alter_table('marks', schema=None) as batch_op:
        batch_op.drop_column('year')
        batch_op.drop_column('term')