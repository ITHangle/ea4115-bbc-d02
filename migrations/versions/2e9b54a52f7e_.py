"""empty message

Revision ID: 2e9b54a52f7e
Revises: fa4af88babd3
Create Date: 2024-04-28 12:53:35.175510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e9b54a52f7e'
down_revision = 'fa4af88babd3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bookmark', schema=None) as batch_op:
        batch_op.drop_constraint('bookmark_news_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'news', ['news_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bookmark', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('bookmark_news_id_fkey', 'news', ['news_id'], ['id'])

    # ### end Alembic commands ###
