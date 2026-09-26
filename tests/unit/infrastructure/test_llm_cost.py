"""Учёт расхода на модель и метка кэша."""

import json
from typing import Any

import httpx2
import pytest
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.application.ports.observability_port import TokenKind
from app.infrastructure import llm_runtime
from app.infrastructure.extractors.vacancy_extractor import GoogleVacancyLLMExtractor
from app.infrastructure.llm import get_resume_parse_agent, get_vacancy_parse_agent
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
        """Вход считается целиком, кэшированные токены — его часть."""
        plain = cost_micro_usd(MODEL, input_tokens=1_000_000)
        cached = cost_micro_usd(MODEL, input_tokens=1_000_000, cache_read_tokens=1_000_000)

        assert plain == pytest.approx(cached * 10, rel=0.01)

    def test_cache_write_costs_no_more_than_input(self) -> None:
        """Промах по кэшу не должен стоить дороже вызова без кэша, иначе включать рискованно.

        Записанные токены Gemini тут же читает из кэша, так что у записи
        они приходят и в cache_read, и в cache_write.
        """
        plain = cost_micro_usd(MODEL, input_tokens=1_000_000)
        written = cost_micro_usd(
            MODEL,
            input_tokens=1_000_000,
            cache_read_tokens=1_000_000,
            cache_write_tokens=1_000_000,
        )

        assert written <= plain

    @pytest.mark.parametrize(
        ("input_tokens", "output_tokens", "cache_read", "cache_write", "billed"),
        [
            (2083, 41, 0, 0, 727),
            (2083, 41, 2027, 0, 180),
            (2080, 33, 2027, 0, 159),
            (2077, 50, 2027, 2027, 370),
        ],
    )
    def test_matches_openrouter_bill(
        self, input_tokens: int, output_tokens: int, cache_read: int, cache_write: int, billed: int
    ) -> None:
        """Живые вызовы 27.09 и списания OpenRouter за них в микродолларах.

        Без кэша, два попадания и запись в протухший кэш. Прежняя формула
        брала за токены из кэша и полную цену, и цену кэша, а запись считала
        как вход: попадание выходило в 788 вместо 180, запись — в 1431 вместо 370.
        """
        cost = cost_micro_usd(
            MODEL,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_write_tokens=cache_write,
        )

        assert cost == billed

    def test_unknown_model_costs_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Неизвестная цена — ноль, а не выдуманное число."""
        monkeypatch.setattr(pricing, "_unknown_reported", set())

        assert cost_micro_usd("who/knows", input_tokens=1_000_000) == 0

    def test_parts_add_up(self) -> None:
        total = cost_micro_usd(MODEL, input_tokens=2000, output_tokens=1000, cache_read_tokens=1000)
        parts = (
            cost_micro_usd(MODEL, input_tokens=1000)
            + cost_micro_usd(MODEL, output_tokens=1000)
            + cost_micro_usd(MODEL, input_tokens=1000, cache_read_tokens=1000)
        )

        assert total == pytest.approx(parts, abs=2)

    @pytest.mark.parametrize("model", sorted(PRICES))
    def test_every_price_is_positive(self, model: str) -> None:
        """Запись в кэш бывает бесплатной, как у OpenAI, остальное — нет."""
        price = PRICES[model]

        assert min(price.input, price.output, price.cache_read) > 0
        assert price.cache_write >= 0


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


# Ответ OpenRouter в минимальном виде: модель вызывает инструмент ответа.
COMPLETION = {
    "id": "gen-test",
    "object": "chat.completion",
    "created": 0,
    "model": MODEL,
    "provider": "Google",
    "choices": [
        {
            "index": 0,
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_0",
                        "type": "function",
                        "function": {"name": "final_result", "arguments": '{"is_vacancy": false}'},
                    }
                ],
            },
        }
    ],
    # usage живого вызова 27.09 с попаданием в кэш — дословно, со всеми
    # полями: учёт ломался как раз на нулевом reasoning_tokens.
    "usage": {
        "prompt_tokens": 2083,
        "completion_tokens": 41,
        "total_tokens": 2124,
        "cost": 0.00018011,
        "is_byok": False,
        "prompt_tokens_details": {
            "cached_tokens": 2027,
            "cache_write_tokens": 0,
            "audio_tokens": 0,
            "video_tokens": 0,
        },
        "cost_details": {
            "upstream_inference_cost": 0.00018011,
            "upstream_inference_prompt_cost": 7.761e-05,
            "upstream_inference_completions_cost": 0.0001025,
        },
        "completion_tokens_details": {"reasoning_tokens": 0, "image_tokens": 0, "audio_tokens": 0},
    },
}


def _recording_model(sent: list[dict[str, Any]]) -> OpenRouterModel:
    def reply(request: httpx2.Request) -> httpx2.Response:
        sent.append(json.loads(request.content))
        return httpx2.Response(200, json=COMPLETION)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply))
    return OpenRouterModel(MODEL, provider=OpenRouterProvider(api_key="test", http_client=client))


class TestPromptCache:
    """Запрос собирает настоящая модель pydantic-ai, подменён только HTTP.

    В v0.16.0 тест смотрел на порядок строк в исходнике, а pydantic-ai
    отбивал каждый такой запрос с UserError, и разбор вакансий на проде
    встал. Ошибки сборки запроса видны только при самой сборке.
    """

    async def _vacancy_request(self) -> dict[str, Any]:
        sent: list[dict[str, Any]] = []
        with get_vacancy_parse_agent().override(model=_recording_model(sent)):
            await GoogleVacancyLLMExtractor().parse_vacancy("Ищем Python-разработчика в платежи")

        assert len(sent) == 1
        return sent[0]

    async def test_vacancy_request_goes_out(self) -> None:
        request = await self._vacancy_request()

        assert request["model"] == MODEL

    async def test_system_prompt_is_cached(self) -> None:
        system = (await self._vacancy_request())["messages"][0]

        assert system["role"] == "system"
        assert system["content"][-1]["cache_control"] == {"type": "ephemeral"}

    async def test_vacancy_text_is_not_cached(self) -> None:
        """Текст вакансии каждый раз новый: под меткой он сорвал бы все попадания."""
        user = (await self._vacancy_request())["messages"][-1]

        assert user["role"] == "user"
        assert "cache_control" not in json.dumps(user)

    def test_resume_parsing_is_not_cached(self) -> None:
        """Резюме грузят единицы раз в месяц: кэш протухнет, а запись оплатится."""
        settings = get_resume_parse_agent().model_settings or {}

        assert "openrouter_cache_instructions" not in settings


class TestUsageRecorded:
    """Расход снимается с ответа, прошедшего через настоящую модель pydantic-ai.

    С genai-prices 0.1 pydantic-ai 1.x молча обнулял usage, и графики расхода
    показывали бы ноль, а тесты на сами счётчики этого не видели.
    """

    async def test_tokens_and_cost_from_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        tokens: dict[TokenKind, int] = {}
        costs: list[tuple[str, int]] = []

        def record_tokens(kind: TokenKind, count: int) -> None:
            tokens[kind] = count

        def record_cost(model: str, micro_usd: int) -> None:
            costs.append((model, micro_usd))

        monkeypatch.setattr(llm_runtime, "observe_llm_tokens", record_tokens)
        monkeypatch.setattr(llm_runtime, "observe_llm_cost", record_cost)

        with get_vacancy_parse_agent().override(model=_recording_model([])):
            await GoogleVacancyLLMExtractor().parse_vacancy("Ищем Python-разработчика в платежи")

        assert tokens == {
            TokenKind.INPUT: 2083,
            TokenKind.OUTPUT: 41,
            TokenKind.CACHE_READ: 2027,
            TokenKind.CACHE_WRITE: 0,
        }
        # Столько же списал OpenRouter за этот вызов: $0.00018011.
        assert costs == [(MODEL, 180)]
