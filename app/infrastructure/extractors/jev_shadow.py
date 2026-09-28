"""Jev рядом с Gemini: тень и фильтр.

Тень: бот живёт только по ответу Gemini. Jev получает тот же текст
параллельно, и её ответ пишется рядом для сравнения: основной путь её не
ждёт, а её ошибки наружу не выходят. Цель — узнать на своих русских
вакансиях, насколько Jev совпадает с Gemini и честна ли её уверенность,
прежде чем доверять ей что-либо решать.

Фильтр: Jev решает первой, и тексты, которые она уверенно считает не
вакансиями, до Gemini не доходят. Пишет в ту же таблицу, что и тень.
"""

import asyncio
import random
from collections.abc import Callable, Coroutine
from enum import StrEnum
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

# Сколько фильтр ждёт Jev, прежде чем отдать текст в Gemini без неё. Здесь
# Jev стоит на основном пути, поэтому запас меньше, чем у тени.
JEV_GATE_WAIT_SECONDS = 10

# От этой вероятности ответ Jev считается «да». Нужен только чтобы решить,
# сохранять ли текст; настоящий порог выбирается по отчёту.
DECISION_THRESHOLD = 0.5

# Середина шкалы — ровно те случаи, по которым потом выбирается порог,
# поэтому их текст тоже сохраняется.
UNCERTAIN_LOW = 0.2
UNCERTAIN_HIGH = 0.8

ERROR_NAME_LENGTH = 64

# Доля совпавших ответов, у которых текст всё равно сохраняется. По ним
# проверяется, не ошибаются ли обе модели одинаково: у совпадений иначе
# текста нет, а у отсеянных сообщений его нет и в таблице вакансий.
AGREEMENT_SAMPLE_RATE = 0.05


class TextReason(StrEnum):
    """Почему у строки сохранён текст.

    Причина пишется явно: ошибки в случайной выборке совпадений при подсчёте
    надо умножать обратно на её долю, а остальные — нет.
    """

    LLM_FAILED = "llm_failed"
    DISAGREE = "disagree"
    UNCERTAIN = "uncertain"
    GRADE = "grade"
    SAMPLE = "sample"


class GateDecision(StrEnum):
    """Что фильтр сделал с текстом.

    AUDIT — текст, который фильтр отсеял бы, но отправил в Gemini для
    контроля. Вакансии среди них — потери фильтра, и на весь поток их надо
    умножать обратно на долю контроля.
    """

    PASSED = "passed"
    SKIPPED = "skipped"
    AUDIT = "audit"
    JEV_FAILED = "jev_failed"


def text_reason(
    decision: JevDecision | None,
    llm: OutVacancyParse | None,
    draw: Callable[[], float] = random.random,
) -> TextReason | None:
    """Текст храним только там, где его придётся читать глазами.

    Хранить тексты сверх нужного — лишнее, даже если это публичные посты
    каналов, поэтому из совпадений сохраняется лишь случайная доля.
    """
    if decision is None:
        return None
    jev_says_vacancy = decision.is_vacancy_probability >= DECISION_THRESHOLD
    if llm is None:
        # Gemini сломался, а Jev видит вакансию — кандидат в потерянные.
        return TextReason.LLM_FAILED if jev_says_vacancy else None
    if jev_says_vacancy != llm.is_vacancy:
        return TextReason.DISAGREE
    if UNCERTAIN_LOW <= decision.is_vacancy_probability <= UNCERTAIN_HIGH:
        return TextReason.UNCERTAIN
    if llm.is_vacancy and decision.grade != llm.grade.value:
        return TextReason.GRADE
    if draw() < AGREEMENT_SAMPLE_RATE:
        return TextReason.SAMPLE
    return None


def build_row(
    text: str,
    decision: JevDecision | None,
    jev_error: str | None,
    llm: OutVacancyParse | None,
    llm_error: str | None,
    draw: Callable[[], float] = random.random,
    gate: GateDecision | None = None,
) -> JevShadowLog:
    reason = text_reason(decision, llm, draw)
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
        text=text if reason is not None else None,
        text_reason=reason.value if reason is not None else None,
        gate=gate.value if gate is not None else None,
    )


def _error_name(exc: BaseException) -> str:
    return type(exc).__name__[:ERROR_NAME_LENGTH]


class _Recorder:
    """Пишет строки сравнения в фоне: запись не тормозит разбор и не роняет его."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._pending: set[asyncio.Task[None]] = set()

    def _spawn(self, coro: Coroutine[Any, Any, None]) -> None:
        task = asyncio.create_task(coro)
        # Без ссылки сборщик мусора может снять задачу на середине.
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def _write(self, row: JevShadowLog) -> None:
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()


class JevShadowVacancyExtractor(_Recorder, IVacancyLLMExtractor):
    def __init__(
        self,
        inner: IVacancyLLMExtractor,
        jev: JevClient,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(session_factory)
        self._inner = inner
        self._jev = jev

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        jev_task = asyncio.create_task(self._jev.decide(text))
        try:
            result = await self._inner.parse_vacancy(text)
        except Exception as exc:
            self._spawn(self._record(jev_task, text, None, _error_name(exc)))
            raise
        self._spawn(self._record(jev_task, text, result, None))
        return result

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

            await self._write(build_row(text, decision, jev_error, llm, llm_error))
        except Exception:
            logger.warning("Jev shadow record failed", exc_info=True)


class JevGateVacancyExtractor(_Recorder, IVacancyLLMExtractor):
    """Jev решает первой: явные «не вакансии» до Gemini не доходят.

    Четыре пятых текстов, дошедших до модели, — не вакансии, и на них
    уходит большая часть вызовов Gemini. Контрольная доля отсеянного всё
    равно идёт в Gemini: по ней видно, сколько вакансий фильтр теряет. Если
    Jev не ответила, текст идёт в Gemini как раньше.
    """

    def __init__(
        self,
        inner: IVacancyLLMExtractor,
        jev: JevClient,
        session_factory: async_sessionmaker[AsyncSession],
        threshold: float,
        audit_rate: float,
        draw: Callable[[], float] = random.random,
    ) -> None:
        super().__init__(session_factory)
        self._inner = inner
        self._jev = jev
        self._threshold = threshold
        self._audit_rate = audit_rate
        self._draw = draw

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        try:
            decision = await asyncio.wait_for(self._jev.decide(text), timeout=JEV_GATE_WAIT_SECONDS)
            jev_error = None
        except Exception as exc:
            decision, jev_error = None, _error_name(exc)

        gate = self.decide_gate(decision)
        if gate is GateDecision.SKIPPED:
            self._spawn(self._record(build_row(text, decision, None, None, None, gate=gate)))
            return OutVacancyParse(is_vacancy=False)

        try:
            result = await self._inner.parse_vacancy(text)
        except Exception as exc:
            row = build_row(text, decision, jev_error, None, _error_name(exc), gate=gate)
            self._spawn(self._record(row))
            raise
        self._spawn(self._record(build_row(text, decision, jev_error, result, None, gate=gate)))
        return result

    def decide_gate(self, decision: JevDecision | None) -> GateDecision:
        if decision is None:
            return GateDecision.JEV_FAILED
        if decision.is_vacancy_probability >= self._threshold:
            return GateDecision.PASSED
        if self._draw() < self._audit_rate:
            return GateDecision.AUDIT
        return GateDecision.SKIPPED

    async def _record(self, row: JevShadowLog) -> None:
        try:
            await self._write(row)
        except Exception:
            logger.warning("Jev gate record failed", exc_info=True)
