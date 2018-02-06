"""empty message

Revision ID: e5b520693de9
Revises: eb2847df33bf
Create Date: 2018-02-06 22:32:08.850171

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e5b520693de9'
down_revision = 'eb2847df33bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.drop_index('ix_submissions_datetime', table_name='submissions')
    op.drop_column('submissions', 'datetime')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('submissions', sa.Column('datetime', postgresql.TIMESTAMP(), server_default=sa.text("'2018-06-02 00:00:00'::timestamp without time zone"), autoincrement=False, nullable=False))
    op.create_index('ix_submissions_datetime', 'submissions', ['datetime'], unique=False)
    op.alter_column('submissions', 'date_time',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    # ### end Alembic commands ###
