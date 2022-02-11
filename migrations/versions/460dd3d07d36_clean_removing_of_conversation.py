"""clean removing of conversation

Revision ID: 460dd3d07d36
Revises: bff429c9329c
Create Date: 2022-02-09 11:28:37.068022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '460dd3d07d36'
down_revision = 'bff429c9329c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('conversations')
    op.drop_table('conversations_users')
    op.drop_table('conversations_messages')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('conversations_messages',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('conversation_id', sa.INTEGER(), nullable=True),
    sa.Column('message_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('conversations_users',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('converation_id', sa.INTEGER(), nullable=True),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['converation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('conversations',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('admin_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
