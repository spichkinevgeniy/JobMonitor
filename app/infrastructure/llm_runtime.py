import asyncio
from collections.abc import Awaitable, Callable

from pydantic_ai.exceptions import ModelHTTPError

from app.core.logger import get_app_logger

logger = get_app_logger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_RETRY_ATTEMPTS = 3
_BASE_DELAY_SECONDS = 1.0


class TemporaryLLMUnavailableError(Exception):
    pass


async def run_with_llm_retry[T](
    operation_name: str,
    runner: Callable[[], Awaitable[T]],
) -> T:
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            return await runner()
        except ModelHTTPError as exc:
            if exc.status_code not in _RETRYABLE_STATUS_CODES:
                raise

            if attempt == _RETRY_ATTEMPTS:
                raise TemporaryLLMUnavailableError(
                    f"LLM temporarily unavailable during {operation_name}"
                ) from exc

            delay_seconds = _BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "LLM provider temporarily unavailable during %s "
                "(status=%s, model=%s, attempt=%s/%s). Retrying in %.1fs",
                operation_name,
                exc.status_code,
                exc.model_name,
                attempt,
                _RETRY_ATTEMPTS,
                delay_seconds,
            )
            await asyncio.sleep(delay_seconds)
