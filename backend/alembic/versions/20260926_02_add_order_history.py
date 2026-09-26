"""add order history

Revision ID: 20260926_02
Revises: 20260926_01
Create Date: 2026-09-26
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260926_02"
down_revision: str | None = "20260926_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "order_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.Enum(
                "IMPORTED",
                "EDITED",
                "APPROVED",
                "REJECTED",
                name="order_history_action",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("details", sa.Text(), nullable=True),
    )
    op.create_index("ix_order_history_order_id", "order_history", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_order_history_order_id", table_name="order_history")
    op.drop_table("order_history")
