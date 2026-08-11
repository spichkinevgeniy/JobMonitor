"""drop cv_text from users

Revision ID: a7b8c9d0e1f2
Revises: e6f7a8b9c0d1
Create Date: 2026-08-10 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: str | Sequence[str] | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Полный текст резюме нигде не читался: подбор идёт по специализациям и
    # навыкам. Хранение без применения — только риск.
    op.drop_column("users", "cv_text")


def downgrade() -> None:
    """Downgrade schema."""
    # Колонка вернётся пустой: тексты удалены безвозвратно.
    op.add_column("users", sa.Column("cv_text", sa.Text(), nullable=True))
