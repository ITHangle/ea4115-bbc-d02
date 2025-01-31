"""empty message

Revision ID: 679ab747ba7d
Revises: 6092228cc420
Create Date: 2024-04-19 13:03:18.876853

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '679ab747ba7d'
down_revision = '6092228cc420'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('news',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('image', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('news')
    # ### end Alembic commands ###
