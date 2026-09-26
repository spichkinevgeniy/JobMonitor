"""Перевод токенов в деньги.

Цены за миллион токенов, каталог OpenRouter. Живут в коде, а не в дашборде:
иначе стоимость считается в двух местах и расходится при смене модели.
"""

from dataclasses import dataclass

from app.core.logger import get_app_logger

logger = get_app_logger(__name__)

MICRO_PER_USD = 1_000_000
TOKENS_PER_UNIT = 1_000_000


@dataclass(frozen=True, slots=True)
class ModelPrice:
    """Доллары за миллион токенов."""

    input: float
    output: float
    cache_read: float
    cache_write: float


# Запись в кэш у Gemini — это только хранение: $1 за миллион токенов в час,
# за 5 минут 0.0833. У OpenAI запись бесплатна.
PRICES: dict[str, ModelPrice] = {
    "google/gemini-2.5-flash": ModelPrice(0.30, 2.50, 0.03, 0.083333),
    "google/gemini-2.5-flash-lite": ModelPrice(0.10, 0.40, 0.01, 0.083333),
    "openai/gpt-5-nano": ModelPrice(0.05, 0.40, 0.005, 0.0),
    "openai/gpt-4.1-nano": ModelPrice(0.10, 0.40, 0.025, 0.0),
    "qwen/qwen3.7-flash": ModelPrice(0.03, 0.13, 0.006, 0.038),
}

_unknown_reported: set[str] = set()


def price_for(model: str) -> ModelPrice | None:
    price = PRICES.get(model)
    if price is None and model not in _unknown_reported:
        _unknown_reported.add(model)
        logger.warning("No price for model %s; cost metric will stay at zero", model)
    return price


def cost_micro_usd(
    model: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> int:
    """Стоимость вызова в микродолларах.

    input_tokens — весь вход, как его отдаёт pydantic-ai: токены из кэша в
    нём уже есть. По полной цене идёт только остаток, иначе попадание в кэш
    оплачивалось бы дважды и выходило дороже промаха. Записанные в кэш
    токены Gemini в том же вызове читает из свежего кэша, поэтому они уже
    есть в cache_read_tokens, а за запись берётся только хранение.

    Целое: счётчики в metric_counter хранят int, а доли цента при сложении
    миллионов токенов теряться не должны.
    """
    price = price_for(model)
    if price is None:
        return 0

    uncached_input = max(input_tokens - cache_read_tokens, 0)
    usd = (
        uncached_input * price.input
        + output_tokens * price.output
        + cache_read_tokens * price.cache_read
        + cache_write_tokens * price.cache_write
    ) / TOKENS_PER_UNIT
    return round(usd * MICRO_PER_USD)
