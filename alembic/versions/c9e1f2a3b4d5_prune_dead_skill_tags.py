"""prune dead skill tags and legacy specialization values

Revision ID: c9e1f2a3b4d5
Revises: f7c1d2e3a4b5
Create Date: 2026-08-02 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9e1f2a3b4d5"
down_revision: str | Sequence[str] | None = "f7c1d2e3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Tags dropped from SkillType: never a discriminating signal in production data.
_DROPPED_SKILLS = (
    "Recommender Systems",
    "DBA",
    "Gameplay Programming",
    "Performance Testing",
)

# Values the LLM invented before the enum was enforced by the output schema.
_LEGACY_SKILLS = ("JavaScript",)
_ALLOWED_SPECIALIZATIONS = (
    "Backend",
    "Frontend",
    "Data Science / ML",
    "Mobile",
    "GameDev",
    "QA",
    "Infrastructure & DevOps",
    "Analytics",
)


def _quoted(values: Sequence[str]) -> str:
    return ", ".join("'" + value.replace("'", "''") + "'" for value in values)


def _filter_array(table: str, column: str, keep_condition: str) -> str:
    return f"""
        UPDATE {table}
        SET {column} = COALESCE(
            (
                SELECT jsonb_agg(value ORDER BY value)
                FROM jsonb_array_elements_text({column}) AS value
                WHERE {keep_condition}
            ),
            '[]'::jsonb
        )
        WHERE EXISTS (
            SELECT 1
            FROM jsonb_array_elements_text({column}) AS value
            WHERE NOT ({keep_condition})
        )
    """


def upgrade() -> None:
    """Upgrade schema."""
    removed_skills = _quoted(_DROPPED_SKILLS + _LEGACY_SKILLS)
    keep_skill = f"value NOT IN ({removed_skills})"
    op.execute(_filter_array("vacancies", "skills", keep_skill))
    op.execute(_filter_array("users", "cv_skills", keep_skill))

    keep_specialization = f"value IN ({_quoted(_ALLOWED_SPECIALIZATIONS)})"
    op.execute(_filter_array("vacancies", "specializations", keep_specialization))
    op.execute(_filter_array("users", "cv_specializations", keep_specialization))


def downgrade() -> None:
    """Downgrade schema."""
    # Removed tag values carry no information that can be reconstructed.
