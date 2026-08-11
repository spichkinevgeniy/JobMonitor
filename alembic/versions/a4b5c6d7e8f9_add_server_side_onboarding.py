"""add server-side onboarding and multi work formats

Revision ID: a4b5c6d7e8f9
Revises: a7b8c9d0e1f2
Create Date: 2026-08-09 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a4b5c6d7e8f9"
down_revision: str | Sequence[str] | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CREATE_COMPATIBILITY_FUNCTION = """
CREATE FUNCTION sync_users_legacy_work_format()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.cv_work_formats IS NULL THEN
            NEW.cv_work_formats := CASE
                WHEN NEW.filter_work_format_mode = 'STRICT'
                     AND NEW.cv_work_format IS NOT NULL
                     AND NEW.cv_work_format <> 'UNDEFINED'
                THEN jsonb_build_array(NEW.cv_work_format)
                ELSE '[]'::jsonb
            END;
        END IF;
    ELSIF (
        NEW.cv_work_format IS DISTINCT FROM OLD.cv_work_format
        OR NEW.filter_work_format_mode IS DISTINCT FROM OLD.filter_work_format_mode
    ) AND NEW.cv_work_formats IS NOT DISTINCT FROM OLD.cv_work_formats THEN
        NEW.cv_work_formats := CASE
            WHEN NEW.filter_work_format_mode = 'STRICT'
                 AND NEW.cv_work_format IS NOT NULL
                 AND NEW.cv_work_format <> 'UNDEFINED'
            THEN jsonb_build_array(NEW.cv_work_format)
            ELSE '[]'::jsonb
        END;
    END IF;
    RETURN NEW;
END;
$$
"""

_CREATE_COMPATIBILITY_TRIGGER = """
CREATE TRIGGER trg_users_legacy_work_format_compat
BEFORE INSERT OR UPDATE OF cv_work_format, filter_work_format_mode, cv_work_formats
ON users
FOR EACH ROW
EXECUTE FUNCTION sync_users_legacy_work_format()
"""


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("cv_work_formats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_draft", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Temporary compatibility mechanism. A later migration can drop this trigger
    # together with the legacy scalar column after the HTML Mini App is retired.
    op.execute(_CREATE_COMPATIBILITY_FUNCTION)
    op.execute(_CREATE_COMPATIBILITY_TRIGGER)

    op.execute(
        """
        UPDATE users
        SET cv_work_formats = CASE
            WHEN filter_work_format_mode = 'STRICT'
                 AND cv_work_format IS NOT NULL
                 AND cv_work_format <> 'UNDEFINED'
            THEN jsonb_build_array(cv_work_format)
            ELSE '[]'::jsonb
        END
        """
    )
    op.execute(
        """
        UPDATE users
        SET onboarding_completed_at = now()
        WHERE onboarding_completed_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_users_legacy_work_format_compat ON users")
    op.execute("DROP FUNCTION IF EXISTS sync_users_legacy_work_format()")
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_draft")
    op.drop_column("users", "cv_work_formats")
