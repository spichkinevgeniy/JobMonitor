"""Глобальный потолок одновременных разборов резюме.

Захват на пользователя в роутере держит одного человека, но не общее
число: десять аккаунтов дают десять параллельных разборов по ~120 МБ
каждый — при 744 МБ свободных на проде это снова OOM.

Слот берётся до скачивания файла: иначе ожидающие держали бы в памяти
по буферу на 15 МБ каждый.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.core.logger import get_app_logger

logger = get_app_logger(__name__)

MAX_CONCURRENT_PARSES = 2
SLOT_WAIT_TIMEOUT_SECONDS = 30

_parse_slots = asyncio.Semaphore(MAX_CONCURRENT_PARSES)


@asynccontextmanager
async def acquire_parse_slot() -> AsyncIterator[bool]:
    """Отдаёт False, если слот не освободился за отведённое время.

    Ждать бесконечно нельзя: очередь растёт молча, а пользователь всё это
    время смотрит на «обрабатываем».
    """
    try:
        await asyncio.wait_for(_parse_slots.acquire(), timeout=SLOT_WAIT_TIMEOUT_SECONDS)
    except TimeoutError:
        logger.warning("Resume rejected: no free parse slot")
        yield False
        return

    try:
        yield True
    finally:
        _parse_slots.release()
