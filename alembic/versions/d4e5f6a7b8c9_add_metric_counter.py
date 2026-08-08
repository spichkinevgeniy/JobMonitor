"""add metric_counter

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-07 21:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Счётчики событий, у которых нет своей таблицы: отсев сообщений, отказы
    # матчера, нажатия в интерфейсе. Хранится агрегат, а не событие: строк
    # столько же, сколько пар «метрика + метка», и таблица не растёт.
    op.create_table(
        "metric_counter",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False, server_default=""),
        sa.Column("value", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("name", "label"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("metric_counter")
