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
    op.alter_column("user_data", "openai_key", new_column_name="name")


def downgrade() -> None:
    op.alter_column("user_data", "name", new_column_name="openai_key")
