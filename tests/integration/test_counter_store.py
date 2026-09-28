"""Счётчики переживают перезапуск: суммы в базе копятся через ON CONFLICT."""

from app.infrastructure.db import async_session_factory
from app.infrastructure.observability.counter_store import PersistentCounterStore

KEY = ("messages_skipped", "duplicate")


async def test_increments_accumulate_across_flushes() -> None:
    store = PersistentCounterStore(async_session_factory)

    store.increment(*KEY, count=2)
    first = await store.flush()
    store.increment(*KEY, count=3)
    second = await store.flush()

    assert first[KEY] == 2
    assert second[KEY] == 5


async def test_new_process_continues_from_saved_sum() -> None:
    """Перезапуск — это новый экземпляр хранилища, сумма должна продолжиться."""
    before_restart = PersistentCounterStore(async_session_factory)
    before_restart.increment(*KEY, count=4)
    await before_restart.flush()

    after_restart = PersistentCounterStore(async_session_factory)
    after_restart.increment(*KEY)

    assert (await after_restart.flush())[KEY] == 5
