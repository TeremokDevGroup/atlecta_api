"""Created user tables

Revision ID: fbb3ed88f0ab
Revises: c584e737e905
Create Date: 2024-04-25 00:23:12.778239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbb3ed88f0ab'
down_revision: Union[str, None] = 'c584e737e905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('email', sa.String(length=320), nullable=False),
                    sa.Column('hashed_password', sa.String(
                        length=1024), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=False),
                    sa.Column('is_superuser', sa.Boolean(), nullable=False),
                    sa.Column('is_verified', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_table('user_profile',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.UUID(), nullable=False),
                    sa.Column('first_name', sa.String(
                        length=150), nullable=False),
                    sa.Column('last_name', sa.String(
                        length=150), nullable=False),
                    sa.Column('age', sa.Integer(), nullable=False),
                    sa.Column('gender', sa.SmallInteger(), nullable=False),
                    sa.Column('height', sa.Integer(), nullable=False),
                    sa.Column('weight', sa.Integer(), nullable=False),
                    sa.Column('test_field', sa.String(
                        length=30), nullable=False),
                    sa.Column('bio', sa.Text(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint(
                        'user_id', name='one_user_to_one_profile')
                    )
    op.create_table('user_profiles_sports',
                    sa.Column('user_profile_id', sa.Integer(), nullable=False),
                    sa.Column('sport_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['sport_id'], ['sport.id']),
                    sa.ForeignKeyConstraint(['user_profile_id'], [
                                            'user_profile.id'], ),
                    sa.PrimaryKeyConstraint('user_profile_id', 'sport_id')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_profiles_sports')
    op.drop_table('user_profile')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
