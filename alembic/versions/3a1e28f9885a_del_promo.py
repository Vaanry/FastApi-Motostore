"""Del promo

Revision ID: 3a1e28f9885a
Revises: 2071b4d55159
Create Date: 2024-12-02 12:17:12.944995

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3a1e28f9885a"
down_revision: Union[str, None] = "2071b4d55159"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_promo_id", table_name="promo")
    op.drop_table("promo")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "promo",
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "is_promo", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
        sa.Column("file", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "downloads", sa.INTEGER(), autoincrement=False, nullable=True
        ),
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("id", name="promo_pkey"),
    )
    op.create_index("ix_promo_id", "promo", ["id"], unique=False)
    # ### end Alembic commands ###
