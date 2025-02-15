"""Reset migration

Revision ID: ff4f695ab10d
Revises: a920245aa323
Create Date: 2025-02-14 18:56:16.980126

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff4f695ab10d'
down_revision = 'a920245aa323'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('change_urls_into_payloads',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=255), nullable=False),
    sa.Column('payload', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('target_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['target_id'], ['target.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('target', schema=None) as batch_op:
        batch_op.add_column(sa.Column('api_key', sa.String(length=255), nullable=True))
        batch_op.alter_column('target_port',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('target_username',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=255),
               nullable=False)
        batch_op.alter_column('target_password',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=255),
               nullable=False)
        batch_op.create_unique_constraint(None, ['api_key'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('target', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.alter_column('target_password',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.alter_column('target_username',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.alter_column('target_port',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.drop_column('api_key')

    op.drop_table('change_urls_into_payloads')
    # ### end Alembic commands ###
