"""add exam_type to marks

Revision ID: 1af2e52f9a98
Revises: 7f023e978bce
Create Date: 2026-07-01 14:37:44.266198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1af2e52f9a98'
down_revision = '7f023e978bce'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('marks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('exam_type', sa.String(20), nullable=False, server_default='Mid Term'))


def downgrade():
    with op.batch_alter_table('marks', schema=None) as batch_op:
        batch_op.drop_column('exam_type')