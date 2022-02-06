"""empty message

Revision ID: dfd729af6adb
Revises: 8b7b9a8638e9
Create Date: 2022-02-06 16:51:19.889211

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dfd729af6adb'
down_revision = '8b7b9a8638e9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('user_messages')
    op.drop_table('messages')
    pass

def downgrade():
    pass
