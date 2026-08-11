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
    """Слот на разбор резюме. False, если не освободился за отведённое время."""
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
