"""add matched skills and feedback to vacancy dispatch log

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f8
Create Date: 2026-08-07 19:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "vacancy_dispatch_log",
        sa.Column(
            "matched_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column("vacancy_dispatch_log", sa.Column("feedback", sa.String(), nullable=True))
    op.add_column(
        "vacancy_dispatch_log",
        sa.Column("feedback_at", sa.DateTime(timezone=True), nullable=True),
    )
    # По vacancy_id ищем строку при нажатии кнопки под вакансией.
    op.create_index(
        "ix_vacancy_dispatch_log_vacancy_id",
        "vacancy_dispatch_log",
        ["vacancy_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_vacancy_dispatch_log_vacancy_id", table_name="vacancy_dispatch_log")
    op.drop_column("vacancy_dispatch_log", "feedback_at")
    op.drop_column("vacancy_dispatch_log", "feedback")
    op.drop_column("vacancy_dispatch_log", "matched_skills")
