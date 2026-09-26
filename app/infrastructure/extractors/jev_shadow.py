"""Теневой прогон Jev рядом с Gemini.

Бот живёт только по ответу Gemini. Jev получает тот же текст параллельно, и
её ответ пишется рядом для сравнения: основной путь её не ждёт, а её ошибки
наружу не выходят. Цель — узнать на своих русских вакансиях, насколько Jev
совпадает с Gemini и честна ли её уверенность, прежде чем доверять ей
что-либо решать.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.dto import OutVacancyParse
from app.application.ports.llm_port import IVacancyLLMExtractor
from app.core.logger import get_app_logger
from app.infrastructure.db.models import JevShadowLog
from app.infrastructure.jev import JevClient, JevDecision

logger = get_app_logger(__name__)

# Сколько запись ждёт ответа Jev. Основной путь не ждёт вовсе, поэтому
# запас щедрый: обычно ответ приходит за полсекунды.
JEV_WAIT_SECONDS = 20

# От этой вероятности ответ Jev считается «да». Нужен только чтобы решить,
# сохранять ли текст; настоящий порог выбирается по отчёту.
DECISION_THRESHOLD = 0.5

# Середина шкалы — ровно те случаи, по которым потом выбирается порог,
# поэтому их текст тоже сохраняется.
UNCERTAIN_LOW = 0.2
UNCERTAIN_HIGH = 0.8

ERROR_NAME_LENGTH = 64


def needs_text(decision: JevDecision | None, llm: OutVacancyParse | None) -> bool:
    """Текст храним только там, где его придётся читать глазами.

    Совпавшие ответы читать незачем, а хранить тексты сверх нужного —
    лишнее, даже если это публичные посты каналов.
    """
    if decision is None:
        return False
    jev_says_vacancy = decision.is_vacancy_probability >= DECISION_THRESHOLD
    if llm is None:
        # Gemini сломался, а Jev видит вакансию — кандидат в потерянные.
        return jev_says_vacancy
    if jev_says_vacancy != llm.is_vacancy:
        return True
    if UNCERTAIN_LOW <= decision.is_vacancy_probability <= UNCERTAIN_HIGH:
        return True
    return llm.is_vacancy and jev_says_vacancy and decision.grade != llm.grade.value


def build_row(
    text: str,
    decision: JevDecision | None,
    jev_error: str | None,
    llm: OutVacancyParse | None,
    llm_error: str | None,
) -> JevShadowLog:
    return JevShadowLog(
        text_length=len(text),
        jev_is_vacancy_p=decision.is_vacancy_probability if decision else None,
        jev_grade=decision.grade if decision else None,
        jev_grade_confidence=decision.grade_confidence if decision else None,
        jev_latency_ms=decision.latency_ms if decision else None,
        jev_input_tokens=decision.input_tokens if decision else None,
        jev_cost_usd=decision.cost_usd if decision else None,
        jev_error=jev_error,
        llm_is_vacancy=llm.is_vacancy if llm else None,
        llm_grade=llm.grade.value if llm else None,
        llm_error=llm_error,
        text=text if needs_text(decision, llm) else None,
    )


def _error_name(exc: BaseException) -> str:
    return type(exc).__name__[:ERROR_NAME_LENGTH]


class JevShadowVacancyExtractor(IVacancyLLMExtractor):
    def __init__(
        self,
        inner: IVacancyLLMExtractor,
        jev: JevClient,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._inner = inner
        self._jev = jev
        self._session_factory = session_factory
        self._pending: set[asyncio.Task[None]] = set()

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        jev_task = asyncio.create_task(self._jev.decide(text))
        try:
            result = await self._inner.parse_vacancy(text)
        except Exception as exc:
            self._spawn(self._record(jev_task, text, None, _error_name(exc)))
            raise
        self._spawn(self._record(jev_task, text, result, None))
        return result

    def _spawn(self, coro: Coroutine[Any, Any, None]) -> None:
        task = asyncio.create_task(coro)
        # Без ссылки сборщик мусора может снять задачу на середине.
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def _record(
        self,
        jev_task: asyncio.Task[JevDecision],
        text: str,
        llm: OutVacancyParse | None,
        llm_error: str | None,
    ) -> None:
        try:
            try:
                decision = await asyncio.wait_for(jev_task, timeout=JEV_WAIT_SECONDS)
                jev_error = None
            except Exception as exc:
                decision, jev_error = None, _error_name(exc)

            async with self._session_factory() as session:
                session.add(build_row(text, decision, jev_error, llm, llm_error))
                await session.commit()
        except Exception:
            logger.warning("Jev shadow record failed", exc_info=True)
