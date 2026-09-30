"""rename jev_shadow_log to jev_gate_log

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-30 23:59:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: str | Sequence[str] | None = "e1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Тень Jev убрана, таблица осталась журналом фильтра. Вместе с ней
# переименовываются индекс и счётчик id, чтобы в схеме не осталось «тени».
RENAMES = (
    ("TABLE", "jev_shadow_log", "jev_gate_log"),
    ("INDEX", "ix_jev_shadow_log_created_at", "ix_jev_gate_log_created_at"),
    ("SEQUENCE", "jev_shadow_log_id_seq", "jev_gate_log_id_seq"),
)


def upgrade() -> None:
    """Upgrade schema."""
    for kind, old, new in RENAMES:
        op.execute(f"ALTER {kind} {old} RENAME TO {new}")
    op.execute(
        "ALTER TABLE jev_gate_log RENAME CONSTRAINT jev_shadow_log_pkey TO jev_gate_log_pkey"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER TABLE jev_gate_log RENAME CONSTRAINT jev_gate_log_pkey TO jev_shadow_log_pkey"
    )
    for kind, old, new in reversed(RENAMES):
        op.execute(f"ALTER {kind} {new} RENAME TO {old}")
