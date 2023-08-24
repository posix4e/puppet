"""renamed openai_key to user

Revision ID: 10ed6e0bd75f
Revises: 
Create Date: 2023-08-24 16:08:47.993002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "10ed6e0bd75f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.add_column('user_data', sa.Column('name', sa.String(), nullable=False))
    # op.create_unique_constraint(None, 'user_data', ['name'])
    # op.drop_column('user_data', 'openai_key')
    op.alter_column("user_data", "openai_key", new_column_name="name")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.add_column('user_data', sa.Column('openai_key', sa.VARCHAR(), nullable=False))
    # op.drop_constraint(None, 'user_data', type_='unique')
    # op.drop_column('user_data', 'name')
    op.alter_column("user_data", "name", new_column_name="openai_key")
    # ### end Alembic commands ###
