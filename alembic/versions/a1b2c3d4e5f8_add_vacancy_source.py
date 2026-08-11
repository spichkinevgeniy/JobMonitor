"""add vacancy source channel and message id

Revision ID: a1b2c3d4e5f8
Revises: e5f6a7b8c9d0
Create Date: 2026-08-07 18:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f8"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Nullable без заполнения: у собранных вакансий источник восстановить неоткуда.
    op.add_column("vacancies", sa.Column("source_channel", sa.String(), nullable=True))
    op.add_column("vacancies", sa.Column("source_message_id", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("vacancies", "source_message_id")
    op.drop_column("vacancies", "source_channel")
