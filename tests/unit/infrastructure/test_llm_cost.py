"""Учёт расхода на модель и метка кэша."""

import pytest
from pydantic_ai import CachePoint

from app.application.ports.observability_port import TokenKind
from app.infrastructure.observability import pricing
from app.infrastructure.observability.pricing import PRICES, cost_micro_usd
from app.infrastructure.observability.service import (
    COUNTER_LLM_COST_MICRO,
    COUNTER_LLM_TOKENS,
    PrometheusObservabilityService,
)

MODEL = "google/gemini-2.5-flash"


class FakeStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int]] = []

    def increment(self, name: str, label: str, count: int = 1) -> None:
        self.calls.append((name, label, count))


class TestPricing:
    def test_input_cost(self) -> None:
        """$0.30 за миллион — миллион токенов стоит 300 000 микродолларов."""
        assert cost_micro_usd(MODEL, input_tokens=1_000_000) == 300_000

    def test_cache_read_is_ten_times_cheaper(self) -> None:
        plain = cost_micro_usd(MODEL, input_tokens=1_000_000)
        cached = cost_micro_usd(MODEL, cache_read_tokens=1_000_000)

        assert plain == pytest.approx(cached * 10, rel=0.01)

    def test_cache_write_barely_costs_more_than_input(self) -> None:
        """Промах по кэшу должен быть почти бесплатным, иначе включать рискованно."""
        plain = cost_micro_usd(MODEL, input_tokens=1_000_000)
        written = cost_micro_usd(MODEL, cache_write_tokens=1_000_000)

        assert written / plain < 1.05

    def test_unknown_model_costs_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Неизвестная цена — ноль, а не выдуманное число."""
        monkeypatch.setattr(pricing, "_unknown_reported", set())

        assert cost_micro_usd("who/knows", input_tokens=1_000_000) == 0

    def test_parts_add_up(self) -> None:
        total = cost_micro_usd(MODEL, input_tokens=1000, output_tokens=1000, cache_read_tokens=1000)
        parts = (
            cost_micro_usd(MODEL, input_tokens=1000)
            + cost_micro_usd(MODEL, output_tokens=1000)
            + cost_micro_usd(MODEL, cache_read_tokens=1000)
        )

        assert total == pytest.approx(parts, abs=2)

    @pytest.mark.parametrize("model", sorted(PRICES))
    def test_every_price_is_positive(self, model: str) -> None:
        price = PRICES[model]

        assert min(price.input, price.output, price.cache_read, price.cache_write) > 0


class TestCounters:
    def test_tokens_recorded_by_kind(self) -> None:
        store = FakeStore()
        service = PrometheusObservabilityService(store)

        service.observe_llm_tokens(TokenKind.CACHE_READ, 3311)

        assert store.calls == [(COUNTER_LLM_TOKENS, "cache_read", 3311)]

    def test_cost_recorded_by_model(self) -> None:
        store = FakeStore()
        service = PrometheusObservabilityService(store)

        service.observe_llm_cost(MODEL, 1234)

        assert store.calls == [(COUNTER_LLM_COST_MICRO, MODEL, 1234)]

    @pytest.mark.parametrize("value", [0, -5])
    def test_nothing_recorded_for_empty_usage(self, value: int) -> None:
        """Нули засоряют метки, а отрицательные значения ломают накопление."""
        store = FakeStore()
        service = PrometheusObservabilityService(store)

        service.observe_llm_tokens(TokenKind.INPUT, value)
        service.observe_llm_cost(MODEL, value)

        assert store.calls == []


class TestCachePoint:
    def test_marker_goes_before_the_text(self) -> None:
        """Метка после текста кэширует и сам текст — попаданий тогда не будет."""
        import inspect

        from app.infrastructure.extractors import vacancy_extractor

        source = inspect.getsource(vacancy_extractor.GoogleVacancyLLMExtractor.parse_vacancy)
        marker = source.index("CachePoint()")
        text = source.index("Проанализируй текст")

        assert marker < text

    def test_resume_parsing_has_no_marker(self) -> None:
        """Резюме грузят единицы раз в месяц: кэш протухнет, а запись оплатится."""
        import inspect

        from app.infrastructure.parsers import pdf_parser

        assert "CachePoint" not in inspect.getsource(pdf_parser)

    def test_marker_is_the_pydantic_ai_one(self) -> None:
        assert CachePoint().ttl == "5m"
