"""Move price to item table

Revision ID: 6bee73cac654
Revises: f32fce9faa1a
Create Date: 2024-11-20 22:22:31.848249

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6bee73cac654"
down_revision = "f32fce9faa1a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("catalog", "price")
    op.add_column("items", sa.Column("price", sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("items", "price")
    op.add_column(
        "catalog",
        sa.Column(
            "price",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    # ### end Alembic commands ###
