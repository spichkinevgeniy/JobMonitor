"""add text_reason to jev_shadow_log

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-09-26 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: str | Sequence[str] | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("jev_shadow_log", sa.Column("text_reason", sa.String(length=16), nullable=True))
    # У строк, записанных до этой миграции, причина выводится из самих
    # ответов по тем же правилам. Случайной выборки тогда ещё не было.
    op.execute(
        """
        update jev_shadow_log set text_reason = case
            when llm_is_vacancy is null then 'llm_failed'
            when (jev_is_vacancy_p >= 0.5) <> llm_is_vacancy then 'disagree'
            when jev_is_vacancy_p between 0.2 and 0.8 then 'uncertain'
            else 'grade'
        end
        where text is not null
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("jev_shadow_log", "text_reason")
