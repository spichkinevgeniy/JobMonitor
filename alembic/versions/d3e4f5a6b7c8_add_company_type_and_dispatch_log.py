"""add company_type and vacancy_dispatch_log

Revision ID: d3e4f5a6b7c8
Revises: c9e1f2a3b4d5
Create Date: 2026-08-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: str | Sequence[str] | None = "c9e1f2a3b4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "vacancies",
        sa.Column("company_type", sa.String(), nullable=False, server_default="UNDEFINED"),
    )

    op.create_table(
        "vacancy_dispatch_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_tg_id", sa.BigInteger(), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "dispatched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_vacancy_dispatch_log_user_tg_id",
        "vacancy_dispatch_log",
        ["user_tg_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_vacancy_dispatch_log_user_tg_id", table_name="vacancy_dispatch_log")
    op.drop_table("vacancy_dispatch_log")
    op.drop_column("vacancies", "company_type")
