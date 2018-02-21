"""empty message

Revision ID: 9fee462f4d5a
Revises: 20fa0db1b8f1
Create Date: 2018-02-21 19:42:09.062460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9fee462f4d5a'
down_revision = '20fa0db1b8f1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('semelect',
    sa.Column('streamid', sa.Integer(), nullable=False),
    sa.Column('semesterid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['semesterid'], ['semester.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['streamid'], ['streams.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('streamid', 'semesterid')
    )
    op.create_unique_constraint(None, 'teachersub', ['userid', 'subjectid'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'teachersub', type_='unique')
    op.drop_table('semelect')
    # ### end Alembic commands ###
