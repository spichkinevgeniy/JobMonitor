"""add grade and experience filters

Revision ID: f7c1d2e3a4b5
Revises: 89d7ab44d1f2
Create Date: 2026-03-22 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7c1d2e3a4b5"
down_revision: str | Sequence[str] | None = "89d7ab44d1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "vacancies",
        sa.Column("grade", sa.String(), nullable=False, server_default="UNDEFINED"),
    )
    op.add_column(
        "vacancies",
        sa.Column("experience_level", sa.String(), nullable=False, server_default="UNDEFINED"),
    )
    op.add_column("users", sa.Column("cv_grade", sa.String(), nullable=True))
    op.add_column(
        "users",
        sa.Column("filter_grade_mode", sa.String(), nullable=False, server_default="SOFT"),
    )
    op.add_column("users", sa.Column("cv_experience_level", sa.String(), nullable=True))
    op.add_column(
        "users",
        sa.Column("filter_experience_mode", sa.String(), nullable=False, server_default="SOFT"),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "filter_experience_mode")
    op.drop_column("users", "cv_experience_level")
    op.drop_column("users", "filter_grade_mode")
    op.drop_column("users", "cv_grade")
    op.drop_column("vacancies", "experience_level")
    op.drop_column("vacancies", "grade")
