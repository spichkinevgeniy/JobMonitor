"""Миграции откатываются до нуля и описывают ту же схему, что и модели."""

from typing import Any

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.infrastructure.db.models import Base
from app.infrastructure.db.session import engine
from tests.integration.conftest import alembic


def test_every_migration_rolls_back_and_forward() -> None:
    """Каждый downgrade рабочий: иначе откатить неудачный релиз не выйдет."""
    alembic("downgrade", "base")
    alembic("upgrade", "head")


async def test_models_match_migrations() -> None:
    """Модель без миграции проходит все юнит-тесты и падает только на проде."""

    def diff(connection: Any) -> list[Any]:
        return compare_metadata(MigrationContext.configure(connection), Base.metadata)

    async with engine.connect() as conn:
        differences = await conn.run_sync(diff)

    assert differences == []
