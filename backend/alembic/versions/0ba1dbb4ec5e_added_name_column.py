"""added name column

Revision ID: 0ba1dbb4ec5e
Revises: 
Create Date: 2023-08-25 17:28:32.754476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0ba1dbb4ec5e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tmp_table",
        sa.Column(
            "id", sa.INTEGER(), nullable=False, autoincrement=True, primary_key=True
        ),
        sa.Column("uid", sa.VARCHAR(), nullable=False, unique=True),
        sa.Column("name", sa.VARCHAR(), nullable=False, default="Default name"),
        sa.Column("openai_key", sa.VARCHAR(), nullable=True, unique=False),
    )

    op.execute(
        "INSERT INTO tmp_table(id, uid, name, openai_key) SELECT id, uid, 'Default name', openai_key FROM user_data"
    )
    op.drop_table("user_data")
    op.rename_table("tmp_table", "user_data")


def downgrade() -> None:
    pass
