"""Счётчики, которые переживают перезапуск процесса.

Метрики Prometheus живут в памяти и обнуляются вместе с процессом. Для
событий без своей таблицы храним агрегат в БД и восстанавливаем из него.
"""

import pytest

from app.application.ports.observability_port import Feature, SkipReason
from app.infrastructure.observability.counter_store import PersistentCounterStore
from app.infrastructure.observability.service import (
    COUNTER_FEATURE_USED,
    COUNTER_MATCH_REJECTED,
    COUNTER_MESSAGES_SKIPPED,
    NoOpObservabilityService,
    PrometheusObservabilityService,
)


class _FailingFactory:
    def __call__(self) -> "_FailingFactory":
        return self

    async def __aenter__(self) -> "_FailingFactory":
        raise RuntimeError("база недоступна")

    async def __aexit__(self, *args: object) -> None:
        return None


@pytest.fixture
def store() -> PersistentCounterStore:
    return PersistentCounterStore(_FailingFactory())  # type: ignore[arg-type]


class TestAccumulation:
    def test_increments_are_summed_per_label(self, store: PersistentCounterStore) -> None:
        store.increment("m", "a")
        store.increment("m", "a", 4)
        store.increment("m", "b")

        assert store._pending == {("m", "a"): 5, ("m", "b"): 1}

    def test_labels_do_not_mix(self, store: PersistentCounterStore) -> None:
        store.increment("one", "x")
        store.increment("two", "x")

        assert store._pending[("one", "x")] == 1
        assert store._pending[("two", "x")] == 1


class TestFlushFailure:
    async def test_pending_survives_a_failed_flush(self, store: PersistentCounterStore) -> None:
        """Иначе окно потеряется молча, а счётчик уедет вниз."""
        store.increment("m", "a", 7)

        totals = await store.flush()

        assert totals == {}
        assert store._pending[("m", "a")] == 7

    async def test_failed_flush_does_not_double_count(self, store: PersistentCounterStore) -> None:
        store.increment("m", "a", 3)

        await store.flush()
        await store.flush()

        assert store._pending[("m", "a")] == 3


class TestServiceRouting:
    def test_events_land_in_their_own_counters(self) -> None:
        store = PersistentCounterStore(_FailingFactory())  # type: ignore[arg-type]
        service = PrometheusObservabilityService(store)

        service.observe_message_skipped(SkipReason.TOO_SHORT)
        service.observe_feature_used(Feature.STATS_OPEN)
        service.observe_match_rejected("grade")

        assert store._pending[(COUNTER_MESSAGES_SKIPPED, "too_short")] == 1
        assert store._pending[(COUNTER_FEATURE_USED, "stats_open")] == 1
        assert store._pending[(COUNTER_MATCH_REJECTED, "grade")] == 1

    def test_works_without_a_store(self) -> None:
        """Метрики можно выключить конфигом — падать при этом нельзя."""
        PrometheusObservabilityService(None).observe_feature_used(Feature.STATS_OPEN)
        NoOpObservabilityService().observe_message_skipped(SkipReason.DUPLICATE)
