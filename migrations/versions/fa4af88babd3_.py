"""empty message

Revision ID: fa4af88babd3
Revises: 0e12efdbad9e
Create Date: 2024-04-27 16:26:13.614704

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa4af88babd3'
down_revision = '0e12efdbad9e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('search_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('query', sa.String(length=100), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('search_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_search_history_timestamp'), ['timestamp'], unique=False)

    op.create_table('bookmark',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('news_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['news_id'], ['news.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bookmark', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bookmark_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bookmark', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_bookmark_timestamp'))

    op.drop_table('bookmark')
    with op.batch_alter_table('search_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_search_history_timestamp'))

    op.drop_table('search_history')
    # ### end Alembic commands ###
