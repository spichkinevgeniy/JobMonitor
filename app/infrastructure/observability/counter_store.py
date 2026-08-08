"""Счётчики, которые переживают перезапуск.

Метрики Prometheus живут в памяти процесса и обнуляются вместе с ним. Для
событий, у которых нет своей таблицы (отсев сообщений, отказы матчера,
нажатия в интерфейсе), храним агрегат в БД.

Пишем не событие, а сумму: нагрузка не зависит от их числа. Хоть тысяча в
минуту — всё равно один пакет строк по числу пар «метрика + метка».
"""

import asyncio
from collections import Counter

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logger import get_app_logger
from app.infrastructure.db.models import MetricCounter

logger = get_app_logger(__name__)

NO_LABEL = ""


class PersistentCounterStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._pending: Counter[tuple[str, str]] = Counter()
        self._lock = asyncio.Lock()

    def increment(self, name: str, label: str = NO_LABEL, count: int = 1) -> None:
        """Копим в памяти. Вызывается из горячих путей, поэтому без await."""
        self._pending[(name, label)] += count

    async def flush(self) -> dict[tuple[str, str], int]:
        """Сливает накопленное и возвращает актуальные суммы из БД.

        Накопленное забираем под замком и до записи: если запись упадёт,
        потеряем одно окно, но не будем считать его дважды.
        """
        async with self._lock:
            pending = self._pending
            self._pending = Counter()

        try:
            async with self._session_factory() as session:
                for (name, label), delta in pending.items():
                    statement = (
                        insert(MetricCounter)
                        .values(name=name, label=label, value=delta)
                        .on_conflict_do_update(
                            index_elements=["name", "label"],
                            set_={"value": MetricCounter.value + delta},
                        )
                    )
                    await session.execute(statement)
                await session.commit()

                rows = (
                    await session.execute(
                        select(MetricCounter.name, MetricCounter.label, MetricCounter.value)
                    )
                ).all()
        except Exception:
            # Возвращаем накопленное обратно: следующая попытка допишет его.
            async with self._lock:
                self._pending.update(pending)
            logger.exception("Failed to flush metric counters")
            return {}

        return {(row.name, row.label): row.value for row in rows}
