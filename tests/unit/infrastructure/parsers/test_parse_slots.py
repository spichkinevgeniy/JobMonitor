"""Глобальный потолок одновременных разборов.

Захват на пользователя держит одного человека, но не общее число: десять
аккаунтов давали десять параллельных разборов по ~120 МБ каждый.
"""

import asyncio

import pytest

from app.infrastructure.parsers import concurrency
from app.infrastructure.parsers.concurrency import MAX_CONCURRENT_PARSES, acquire_parse_slot


@pytest.fixture(autouse=True)
def fast_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(concurrency, "SLOT_WAIT_TIMEOUT_SECONDS", 0.05)


async def test_admits_only_max_concurrent() -> None:
    release = asyncio.Event()
    inside = 0
    peak = 0

    async def worker() -> bool:
        nonlocal inside, peak
        async with acquire_parse_slot() as granted:
            if not granted:
                return False
            inside += 1
            peak = max(peak, inside)
            await release.wait()
            inside -= 1
            return True

    tasks = [asyncio.create_task(worker()) for _ in range(10)]
    await asyncio.sleep(0.01)
    assert inside == MAX_CONCURRENT_PARSES

    release.set()
    results = await asyncio.gather(*tasks)

    # Одновременно — не больше потолка, но дождавшиеся всё же обслуживаются:
    # семафор ограничивает параллельность, а не общее число разборов.
    assert peak == MAX_CONCURRENT_PARSES
    assert all(results)


async def test_refuses_instead_of_queueing_forever() -> None:
    release = asyncio.Event()

    async def holder() -> None:
        async with acquire_parse_slot():
            await release.wait()

    holders = [asyncio.create_task(holder()) for _ in range(MAX_CONCURRENT_PARSES)]
    await asyncio.sleep(0.01)

    async with acquire_parse_slot() as granted:
        assert granted is False

    release.set()
    await asyncio.gather(*holders)


async def test_slots_survive_refused_waiters() -> None:
    """Отменённый по таймауту acquire не должен съедать разрешение."""
    release = asyncio.Event()

    async def holder() -> None:
        async with acquire_parse_slot():
            await release.wait()

    holders = [asyncio.create_task(holder()) for _ in range(MAX_CONCURRENT_PARSES)]
    await asyncio.sleep(0.01)

    async def refused() -> bool:
        async with acquire_parse_slot() as granted:
            return granted

    assert await asyncio.gather(*(refused() for _ in range(30))) == [False] * 30

    release.set()
    await asyncio.gather(*holders)

    granted_after = []
    for _ in range(MAX_CONCURRENT_PARSES):
        async with acquire_parse_slot() as granted:
            granted_after.append(granted)

    assert all(granted_after)


async def test_slot_is_released_on_error() -> None:
    with pytest.raises(RuntimeError):
        async with acquire_parse_slot() as granted:
            assert granted
            raise RuntimeError("разбор упал")

    async with acquire_parse_slot() as granted:
        assert granted
