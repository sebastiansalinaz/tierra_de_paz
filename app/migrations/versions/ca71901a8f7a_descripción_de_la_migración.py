"""descripción de la migración

Revision ID: ca71901a8f7a
Revises: 
Create Date: 2024-02-20 18:17:20.437654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca71901a8f7a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('catalogo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.String(length=100), nullable=True),
    sa.Column('fecha_registro', sa.DateTime(), nullable=True),
    sa.Column('archivo', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('documento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.String(length=100), nullable=True),
    sa.Column('fecha_registro', sa.DateTime(), nullable=True),
    sa.Column('archivo', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('usuario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('correo', sa.String(length=100), nullable=False),
    sa.Column('contraseña', sa.String(length=400), nullable=False),
    sa.Column('foto_perfil', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('correo')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('usuario')
    op.drop_table('documento')
    op.drop_table('catalogo')
    # ### end Alembic commands ###
