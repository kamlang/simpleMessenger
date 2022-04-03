"""fixing typo

Revision ID: c09b511a8030
Revises: 97df8334f27c
Create Date: 2022-03-10 09:46:02.219725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c09b511a8030'
down_revision = '97df8334f27c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('conversations_users', 'converation_id', new_column_name='conversation_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('conversations_users', 'conversation_id', new_column_name='converation_id')

    # ### end Alembic commands ###
