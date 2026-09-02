import asyncio
from collections.abc import Awaitable, Callable

from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.run import AgentRunResult

from app.application.ports.observability_port import TokenKind
from app.core.logger import get_app_logger
from app.infrastructure.observability.current import observe_llm_cost, observe_llm_tokens
from app.infrastructure.observability.metrics import LLM_ERRORS_TOTAL
from app.infrastructure.observability.pricing import cost_micro_usd

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
            result = await runner()
            _record_usage(result)
            return result
        except ModelHTTPError as exc:
            LLM_ERRORS_TOTAL.labels(
                operation=operation_name,
                reason=f"http_{exc.status_code}",
            ).inc()
            if exc.status_code not in _RETRYABLE_STATUS_CODES:
                logger.error(
                    "LLM call failed permanently during %s (status=%s, model=%s): %s",
                    operation_name,
                    exc.status_code,
                    exc.model_name,
                    exc.body,
                )
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
        except Exception as exc:
            LLM_ERRORS_TOTAL.labels(
                operation=operation_name,
                reason=type(exc).__name__,
            ).inc()
            raise

    raise TemporaryLLMUnavailableError(f"LLM temporarily unavailable during {operation_name}")


def _record_usage(result: object) -> None:
    """Считает расход по факту ответа: провайдер сам сообщает, что попало в кэш.

    Ошибка учёта не должна ронять разбор, поэтому всё внутри try.
    """
    if not isinstance(result, AgentRunResult):
        return
    try:
        usage = result.usage()
        model = getattr(result.response, "model_name", None) or "unknown"
        counts = {
            TokenKind.INPUT: usage.input_tokens,
            TokenKind.OUTPUT: usage.output_tokens,
            TokenKind.CACHE_READ: usage.cache_read_tokens,
            TokenKind.CACHE_WRITE: usage.cache_write_tokens,
        }
        for kind, tokens in counts.items():
            observe_llm_tokens(kind, int(tokens or 0))
        observe_llm_cost(
            model,
            cost_micro_usd(
                model,
                input_tokens=int(usage.input_tokens or 0),
                output_tokens=int(usage.output_tokens or 0),
                cache_read_tokens=int(usage.cache_read_tokens or 0),
                cache_write_tokens=int(usage.cache_write_tokens or 0),
            ),
        )
    except Exception:
        logger.debug("Failed to record LLM usage", exc_info=True)
