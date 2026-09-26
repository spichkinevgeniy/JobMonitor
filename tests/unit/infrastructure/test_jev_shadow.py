"""Теневой прогон Jev: не влияет на основной путь и пишет нужное для сравнения."""

import asyncio
import json
from typing import Any

import httpx
import pytest

from app.application.dto import OutVacancyParse
from app.core.config import config
from app.domain.shared.value_objects import Grade
from app.infrastructure.extractors import jev_shadow
from app.infrastructure.extractors.jev_shadow import (
    JevShadowVacancyExtractor,
    build_row,
    needs_text,
)
from app.infrastructure.jev import (
    SYSTEM_ONE_URL,
    JevClient,
    JevDecision,
    JevError,
    build_request,
    parse_decision,
)

TEXT = "Ищем Senior Python-разработчика в финтех. Удалённо, 350 тыс. ₽. Резюме: @hr"

# Ответ, снятый с живого запроса к typesafe/jev-1.13 через OpenRouter.
LIVE_RESPONSE: dict[str, Any] = {
    "model": "typesafe/jev-1.13-20260917",
    "answers": {
        "is_vacancy": {"type": "noul", "noul": 0.94},
        "grade": {
            "type": "choice",
            "choice": "SENIOR",
            "probabilities": {"SENIOR": 1, "MIDDLE": 0, "UNDEFINED": 0},
            "confidence": 1,
        },
    },
    "usage": {"input_tokens": 504, "output_tokens": 90, "cost": 2.1168e-05},
    "provider": "TypeSafe",
}


def decision(p: float = 0.94, grade: str = "SENIOR") -> JevDecision:
    return JevDecision(
        is_vacancy_probability=p,
        grade=grade,
        grade_confidence=1.0,
        input_tokens=504,
        cost_usd=2.1e-05,
        latency_ms=320,
    )


def gemini(is_vacancy: bool = True, grade: Grade = Grade.SENIOR) -> OutVacancyParse:
    return OutVacancyParse(is_vacancy=is_vacancy, grade=grade)


class TestRequestAndResponse:
    def test_asks_both_questions_in_one_request(self) -> None:
        """Вопросы в одном запросе тарифицируются один раз — проверено вживую."""
        body = build_request("typesafe/jev-1.13", TEXT)

        assert body["model"] == "typesafe/jev-1.13"
        assert body["state"] == {"message": TEXT}
        assert body["questions"]["is_vacancy"]["type"] == "noul"
        assert body["questions"]["grade"]["type"] == "choice"

    def test_grade_options_match_domain(self) -> None:
        """Иначе ответ Jev не сравнить с грейдом Gemini."""
        options = set(build_request("m", TEXT)["questions"]["grade"]["criteria"])

        assert options == {grade.value for grade in Grade}

    def test_parses_live_response(self) -> None:
        parsed = parse_decision(LIVE_RESPONSE, latency_ms=826)

        assert parsed.is_vacancy_probability == 0.94
        assert parsed.grade == "SENIOR"
        assert parsed.grade_confidence == 1.0
        assert parsed.input_tokens == 504
        assert parsed.cost_usd == pytest.approx(2.1168e-05)
        assert parsed.latency_ms == 826

    def test_cost_is_optional(self) -> None:
        payload = {**LIVE_RESPONSE, "usage": {"input_tokens": 500}}

        assert parse_decision(payload, 1).cost_usd is None

    def test_unexpected_shape_is_an_error(self) -> None:
        with pytest.raises(JevError):
            parse_decision({"answers": {}}, 1)


class TestClient:
    @pytest.mark.asyncio
    async def test_posts_to_openrouter_and_parses(self) -> None:
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json=LIVE_RESPONSE)

        client = JevClient(
            "key", "typesafe/jev-1.13", httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )
        result = await client.decide(TEXT)

        assert str(seen[0].url) == SYSTEM_ONE_URL
        assert json.loads(seen[0].content)["model"] == "typesafe/jev-1.13"
        assert result.is_vacancy_probability == 0.94

    @pytest.mark.asyncio
    async def test_http_error_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, text="rate limited")

        client = JevClient("key", "m", httpx.AsyncClient(transport=httpx.MockTransport(handler)))

        with pytest.raises(JevError, match="429"):
            await client.decide(TEXT)


class TestWhenTextIsKept:
    def test_agreement_keeps_no_text(self) -> None:
        assert needs_text(decision(0.97), gemini(True)) is False

    def test_disagreement_keeps_text(self) -> None:
        assert needs_text(decision(0.1), gemini(True)) is True
        assert needs_text(decision(0.9), gemini(False)) is True

    def test_uncertain_band_keeps_text(self) -> None:
        """По середине шкалы потом выбирается порог — её надо читать."""
        assert needs_text(decision(0.65), gemini(True)) is True

    def test_grade_disagreement_keeps_text(self) -> None:
        assert needs_text(decision(0.97, "MIDDLE"), gemini(True, Grade.SENIOR)) is True

    def test_gemini_failure_with_jev_vacancy_keeps_text(self) -> None:
        """Сломался Gemini, а Jev видит вакансию — кандидат в потерянные."""
        assert needs_text(decision(0.9), None) is True
        assert needs_text(decision(0.05), None) is False

    def test_jev_failure_keeps_no_text(self) -> None:
        assert needs_text(None, gemini(True)) is False

    def test_row_carries_both_answers(self) -> None:
        row = build_row(TEXT, decision(0.1), None, gemini(True), None)

        assert row.jev_is_vacancy_p == 0.1
        assert row.llm_is_vacancy is True
        assert row.llm_grade == "SENIOR"
        assert row.text == TEXT
        assert row.text_length == len(TEXT)


class FakeInner:
    def __init__(
        self, result: OutVacancyParse | None = None, error: Exception | None = None
    ) -> None:
        self.result = result or gemini()
        self.error = error

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        if self.error is not None:
            raise self.error
        return self.result


class FakeJev:
    def __init__(self, delay: float = 0.0, error: Exception | None = None) -> None:
        self.delay = delay
        self.error = error
        self.finished = asyncio.Event()

    async def decide(self, text: str) -> JevDecision:
        await asyncio.sleep(self.delay)
        self.finished.set()
        if self.error is not None:
            raise self.error
        return decision()


class FakeSession:
    def __init__(self, sink: list[Any]) -> None:
        self.sink = sink

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    def add(self, row: Any) -> None:
        self.sink.append(row)

    async def commit(self) -> None:
        return None


def make(inner: FakeInner, jev: FakeJev) -> tuple[JevShadowVacancyExtractor, list[Any]]:
    rows: list[Any] = []
    extractor = JevShadowVacancyExtractor(inner, jev, lambda: FakeSession(rows))  # type: ignore[arg-type]
    return extractor, rows


async def drain(extractor: JevShadowVacancyExtractor) -> None:
    while extractor._pending:
        await asyncio.gather(*extractor._pending)


class TestShadowNeverAffectsTheBot:
    @pytest.mark.asyncio
    async def test_returns_gemini_answer_unchanged(self) -> None:
        expected = gemini(False)
        extractor, _ = make(FakeInner(expected), FakeJev())

        assert await extractor.parse_vacancy(TEXT) is expected

    @pytest.mark.asyncio
    async def test_does_not_wait_for_slow_jev(self) -> None:
        """Основной путь не ждёт Jev: ответ Gemini уходит дальше сразу."""
        jev = FakeJev(delay=0.5)
        extractor, rows = make(FakeInner(), jev)

        await asyncio.wait_for(extractor.parse_vacancy(TEXT), timeout=0.2)

        assert not jev.finished.is_set()
        await drain(extractor)
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_jev_failure_is_swallowed_and_recorded(self) -> None:
        extractor, rows = make(FakeInner(), FakeJev(error=RuntimeError("down")))

        result = await extractor.parse_vacancy(TEXT)
        await drain(extractor)

        assert result.is_vacancy is True
        assert rows[0].jev_error == "RuntimeError"
        assert rows[0].jev_is_vacancy_p is None

    @pytest.mark.asyncio
    async def test_gemini_failure_still_propagates(self) -> None:
        """Сломанный Gemini должен ломаться как раньше — тень его не спасает."""
        extractor, rows = make(FakeInner(error=ValueError("bad")), FakeJev())

        with pytest.raises(ValueError):
            await extractor.parse_vacancy(TEXT)
        await drain(extractor)

        assert rows[0].llm_error == "ValueError"
        assert rows[0].llm_is_vacancy is None

    @pytest.mark.asyncio
    async def test_slow_jev_times_out_without_hanging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(jev_shadow, "JEV_WAIT_SECONDS", 0.05)
        extractor, rows = make(FakeInner(), FakeJev(delay=1.0))

        await extractor.parse_vacancy(TEXT)
        await drain(extractor)

        assert rows[0].jev_error == "TimeoutError"

    @pytest.mark.asyncio
    async def test_storage_failure_is_swallowed(self) -> None:
        class BrokenSession(FakeSession):
            async def commit(self) -> None:
                raise ConnectionError("db down")

        extractor = JevShadowVacancyExtractor(
            FakeInner(),
            FakeJev(),
            lambda: BrokenSession([]),  # type: ignore[arg-type]
        )

        result = await extractor.parse_vacancy(TEXT)
        await drain(extractor)

        assert result.is_vacancy is True


class TestSwitch:
    def test_disabled_by_default(self) -> None:
        assert type(config).model_fields["JEV_SHADOW_ENABLED"].default is False

    def test_flag_reaches_the_container(self) -> None:
        """Переменные в compose перечислены поимённо: без записи флаг не долетит."""
        from pathlib import Path

        compose = Path("docker-compose.yml").read_text(encoding="utf-8")

        assert "JEV_SHADOW_ENABLED" in compose
        assert "JEV_MODEL" in compose

    def test_bootstrap_wraps_only_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.bootstrap import bootstrap
        from app.infrastructure.extractors.vacancy_extractor import GoogleVacancyLLMExtractor

        monkeypatch.setattr(bootstrap, "GoogleVacancyLLMExtractor", lambda: FakeInner())
        monkeypatch.setattr(config, "JEV_SHADOW_ENABLED", False)
        assert not isinstance(bootstrap.build_vacancy_extractor(), JevShadowVacancyExtractor)

        monkeypatch.setattr(config, "JEV_SHADOW_ENABLED", True)
        assert isinstance(bootstrap.build_vacancy_extractor(), JevShadowVacancyExtractor)
        assert GoogleVacancyLLMExtractor is not None
