"""Remove Logs table

Revision ID: ecd5157b2124
Revises: 6bee73cac654
Create Date: 2024-11-21 14:57:04.564178

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ecd5157b2124"
down_revision = "6bee73cac654"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_logs_id", table_name="logs")
    op.drop_table("logs")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "logs",
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("tg_id", sa.BIGINT(), autoincrement=False, nullable=True),
        sa.Column("button", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["tg_id"],
            ["users.tg_id"],
            name="logs_tg_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="logs_pkey"),
    )
    op.create_index("ix_logs_id", "logs", ["id"], unique=False)
    # ### end Alembic commands ###
