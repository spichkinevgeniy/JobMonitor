"""Клиент Jev — модели TypeSafe, которая отвечает вероятностями, а не текстом.

Ходит через OpenRouter: ключ и оплата там уже есть, отдельный аккаунт в
TypeSafe не нужен. Готовая интеграция pydantic-ai работает только с их
собственным ключом, поэтому здесь свой небольшой клиент.
"""

import time
from dataclasses import dataclass
from typing import Any

import httpx

SYSTEM_ONE_URL = "https://openrouter.ai/api/v1/systemone"
REQUEST_TIMEOUT_SECONDS = 15

# Критерии повторяют промпт Gemini: сравнение имеет смысл, только если обе
# модели отвечают на один и тот же вопрос. Инструкции на английском, текст
# вакансии остаётся русским — на живом запросе так и проверено.
IS_VACANCY_INSTRUCTIONS = (
    "The text is a job posting in which an employer, recruiter or client is hiring "
    "for one specific IT role. It must name the role or specialist being sought and "
    "contain at least one hiring detail: requirements, duties, working conditions, "
    "salary, work format, company description, how to apply, or a contact for "
    "candidates. Answer no if the text is a resume or a candidate profile, someone "
    "offering their own services or looking for projects, a list of technologies or "
    "a portfolio without a hiring context, written in the first person to promote the "
    "author, a digest or list of several vacancies, roles or companies, or if there "
    "is no clear employer or hiring request. When the signals are mixed, answer no."
)

GRADE_INSTRUCTIONS = (
    "Seniority level of the role in the job posting, judged by the role title and "
    "the stated requirements."
)

GRADE_CRITERIA = {
    "INTERN": "internship or trainee position",
    "JUNIOR": "junior level",
    "MIDDLE": "middle level",
    "SENIOR": "senior level",
    "LEAD": "lead, head of, principal or architect",
    "UNDEFINED": "the level is not stated and cannot be determined",
}


class JevError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class JevDecision:
    is_vacancy_probability: float
    grade: str
    grade_confidence: float
    input_tokens: int
    cost_usd: float | None
    latency_ms: int


def build_request(model: str, text: str) -> dict[str, Any]:
    return {
        "model": model,
        "state": {"message": text},
        "questions": {
            "is_vacancy": {"type": "noul", "instructions": IS_VACANCY_INSTRUCTIONS},
            "grade": {
                "type": "choice",
                "instructions": GRADE_INSTRUCTIONS,
                "criteria": GRADE_CRITERIA,
            },
        },
    }


def parse_decision(payload: dict[str, Any], latency_ms: int) -> JevDecision:
    try:
        answers = payload["answers"]
        grade = answers["grade"]
        usage = payload.get("usage") or {}
        return JevDecision(
            is_vacancy_probability=float(answers["is_vacancy"]["noul"]),
            grade=str(grade["choice"]),
            grade_confidence=float(grade["confidence"]),
            input_tokens=int(usage.get("input_tokens", 0)),
            cost_usd=float(usage["cost"]) if usage.get("cost") is not None else None,
            latency_ms=latency_ms,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise JevError(f"Unexpected response shape: {exc!r}") from exc


class JevClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._client = client or httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def decide(self, text: str) -> JevDecision:
        started = time.perf_counter()
        response = await self._client.post(SYSTEM_ONE_URL, json=build_request(self._model, text))
        latency_ms = round((time.perf_counter() - started) * 1000)
        if response.status_code != 200:
            raise JevError(f"HTTP {response.status_code}: {response.text[:200]}")
        return parse_decision(response.json(), latency_ms)

    async def close(self) -> None:
        await self._client.aclose()
