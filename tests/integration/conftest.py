"""Интеграционные тесты на настоящем Postgres.

Юнит-тесты не видят того, что делает сама база: операторы JSONB в
предфильтре подбора, ON CONFLICT в счётчиках, уникальность текста вакансии,
сами миграции. Здесь это проверяется на живом Postgres.

Нужна база, которую не жалко: тесты сносят схему до нуля, накатывают
миграции заново и чистят таблицы перед каждым тестом. Поэтому запускаются
они только при INTEGRATION_DB=1, а адрес берут из обычных POSTGRES_* —
тех же, что у приложения. Локально:

    docker run --rm -d --name jm-it-pg -p 55432:5432 -e POSTGRES_USER=test \\
        -e POSTGRES_PASSWORD=test -e POSTGRES_DB=jm_test postgres:16-alpine
    INTEGRATION_DB=1 POSTGRES_SERVER=localhost POSTGRES_PORT=55432 \\
        POSTGRES_USER=test POSTGRES_PASSWORD=test POSTGRES_DB=jm_test \\
        uv run -m pytest tests/integration -q
"""

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import text

INTEGRATION_DIR = Path(__file__).parent
ROOT = INTEGRATION_DIR.parents[1]
ENABLED = os.environ.get("INTEGRATION_DB") == "1"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if ENABLED:
        return
    skip = pytest.mark.skip(reason="нужен Postgres: INTEGRATION_DB=1 и POSTGRES_*, см. conftest")
    for item in items:
        if INTEGRATION_DIR in item.path.parents:
            item.add_marker(skip)


def alembic(*args: str) -> None:
    """Миграции — отдельным процессом: env.py сам запускает цикл событий."""
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT,
        check=True,
        env=os.environ.copy(),
    )


@pytest.fixture(scope="session", autouse=True)
def migrated_schema() -> None:
    """Схема с нуля: всё, что осталось от прошлых прогонов, сносится."""
    if not ENABLED:
        return
    database = os.environ.get("POSTGRES_DB", "")
    if "test" not in database:
        # Тесты сносят схему целиком: перепутанный POSTGRES_DB стёр бы
        # рабочую базу. Имя тестовой базы обязано говорить само за себя.
        pytest.exit(f"Интеграционные тесты сносят схему: база «{database}» не похожа на тестовую")
    alembic("downgrade", "base")
    alembic("upgrade", "head")


@pytest.fixture(autouse=True)
async def clean_tables() -> AsyncIterator[None]:
    """Каждый тест начинает с пустых таблиц."""
    if not ENABLED:
        yield
        return

    from app.infrastructure.db.models import Base
    from app.infrastructure.db.session import engine

    names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    yield
