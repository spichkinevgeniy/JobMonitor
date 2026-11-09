"""add users.deactivated_at

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-11-09 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: str | Sequence[str] | None = "f2a3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))
    # Раньше дату не хранили. У тех, кто уже ушёл, ближайшая оценка — последняя
    # доставка: о блокировке бот узнаёт на одной из следующих отправок. Кто не
    # получил ни одной вакансии, остаётся без даты: её неоткуда взять.
    op.execute(
        """
        update users u
        set deactivated_at = d.last_dispatched_at
        from (
            select user_tg_id, max(dispatched_at) as last_dispatched_at
            from vacancy_dispatch_log
            group by user_tg_id
        ) d
        where u.tg_id = d.user_tg_id and not u.is_active
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "deactivated_at")
