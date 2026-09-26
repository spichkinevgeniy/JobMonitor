"""add jev_shadow_log

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-09-26 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: str | Sequence[str] | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Временная таблица эксперимента с Jev: после выбора порога удаляется
    # отдельной миграцией.
    op.create_table(
        "jev_shadow_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("jev_is_vacancy_p", sa.Float(), nullable=True),
        sa.Column("jev_grade", sa.String(length=16), nullable=True),
        sa.Column("jev_grade_confidence", sa.Float(), nullable=True),
        sa.Column("jev_latency_ms", sa.Integer(), nullable=True),
        sa.Column("jev_input_tokens", sa.Integer(), nullable=True),
        sa.Column("jev_cost_usd", sa.Float(), nullable=True),
        sa.Column("jev_error", sa.String(length=64), nullable=True),
        sa.Column("llm_is_vacancy", sa.Boolean(), nullable=True),
        sa.Column("llm_grade", sa.String(length=16), nullable=True),
        sa.Column("llm_error", sa.String(length=64), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
    )
    op.create_index("ix_jev_shadow_log_created_at", "jev_shadow_log", ["created_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_jev_shadow_log_created_at", table_name="jev_shadow_log")
    op.drop_table("jev_shadow_log")
