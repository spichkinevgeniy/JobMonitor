"""add resume_import_job

Revision ID: b1c2d3e4f5a6
Revises: a4b5c6d7e8f9
Create Date: 2026-08-14 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a4b5c6d7e8f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Только статус разбора: содержимое резюме здесь не хранится.
    op.create_table(
        "resume_import_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_tg_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_resume_import_job_user_tg_id"), "resume_import_job", ["user_tg_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_resume_import_job_user_tg_id"), table_name="resume_import_job")
    op.drop_table("resume_import_job")
