"""add weekly pulse

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-09-29 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "d0e1f2a3b4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Сводка включена всем, кто уже есть: отписаться можно из неё самой.
    op.add_column(
        "users",
        sa.Column("pulse_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "weekly_pulse_log",
        sa.Column("user_tg_id", sa.BigInteger(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_tg_id", "week_start"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("weekly_pulse_log")
    op.drop_column("users", "pulse_enabled")
