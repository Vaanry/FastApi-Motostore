"""Add password

Revision ID: 3637cd9a8021
Revises: 207b7cee3779
Create Date: 2024-11-22 14:02:26.438565

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3637cd9a8021"
down_revision: Union[str, None] = "207b7cee3779"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users", sa.Column("hashed_password", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "hashed_password")
    # ### end Alembic commands ###
