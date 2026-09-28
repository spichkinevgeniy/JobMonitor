"""Рассылка недельной сводки всем, кто её не отключил."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup

from app.application.ports.observability_port import Feature
from app.application.ports.unit_of_work import UserUnitOfWork, VacancyUnitOfWork
from app.application.services.weekly_pulse_service import PulseWeek, WeeklyPulseService
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.domain.user.entities import User
from app.infrastructure.observability import observe_feature
from app.telegram.bot.delivery import deactivate_user
from app.telegram.bot.keyboards import get_pulse_kb
from app.telegram.bot.views.pulse import build_weekly_pulse_text

logger = get_app_logger(__name__)

SEND_DELAY_SECONDS = 0.05


class PulseStatus(StrEnum):
    SENT = "sent"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(slots=True)
class PulseRunResult:
    sent: int = 0
    skipped: int = 0
    blocked: int = 0
    failed: int = 0
    already_done: int = 0

    def add(self, status: PulseStatus | None) -> None:
        if status is None:
            self.already_done += 1
        else:
            setattr(self, status.value, getattr(self, status.value) + 1)


class WeeklyPulseSender:
    def __init__(
        self,
        bot: Bot,
        user_uow_factory: Callable[[], UserUnitOfWork],
        vacancy_uow_factory: Callable[[], VacancyUnitOfWork],
        stats_url: str,
        deactivate: Callable[[int], Awaitable[None]] = deactivate_user,
        delay_seconds: float = SEND_DELAY_SECONDS,
    ) -> None:
        self._bot = bot
        self._user_uow = user_uow_factory
        self._vacancy_uow = vacancy_uow_factory
        self._stats_url = stats_url
        self._deactivate = deactivate
        self._delay_seconds = delay_seconds

    async def run(self, week: PulseWeek) -> PulseRunResult:
        """Безопасно запускать повторно: неделя, занятая за человеком, пропускается."""
        uow = self._user_uow()
        async with uow:
            users = await uow.users.list_pulse_recipients()

        result = PulseRunResult()
        for user in users:
            result.add(await self._process(user, week))

        if result.sent or result.skipped or result.blocked or result.failed:
            logger.info(
                "Weekly pulse for %s: sent=%d skipped=%d blocked=%d failed=%d already=%d",
                week.start_date,
                result.sent,
                result.skipped,
                result.blocked,
                result.failed,
                result.already_done,
            )
        return result

    async def _process(self, user: User, week: PulseWeek) -> PulseStatus | None:
        tg_id = user.tg_id.value
        uow = self._user_uow()
        async with uow:
            if not await uow.users.claim_weekly_pulse(tg_id, week.start_date):
                return None

        status = await self._deliver(user, week)
        uow = self._user_uow()
        async with uow:
            await uow.users.set_weekly_pulse_status(tg_id, week.start_date, status.value)
        return status

    async def _deliver(self, user: User, week: PulseWeek) -> PulseStatus:
        tg_id = user.tg_id.value
        try:
            pulse = await WeeklyPulseService(self._vacancy_uow()).build(user, week)
        except Exception:
            logger.exception("Weekly pulse build failed for user %s", user_ref(tg_id))
            return PulseStatus.FAILED

        if not pulse.worth_sending:
            return PulseStatus.SKIPPED

        try:
            await self._send(tg_id, build_weekly_pulse_text(pulse), get_pulse_kb(self._stats_url))
        except TelegramForbiddenError:
            await self._deactivate(tg_id)
            return PulseStatus.BLOCKED
        except Exception:
            logger.exception("Weekly pulse send failed for user %s", user_ref(tg_id))
            return PulseStatus.FAILED

        observe_feature(Feature.PULSE_SENT)
        await asyncio.sleep(self._delay_seconds)
        return PulseStatus.SENT

    async def _send(self, tg_id: int, text: str, markup: InlineKeyboardMarkup) -> None:
        try:
            await self._bot.send_message(chat_id=tg_id, text=text, reply_markup=markup)
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            await self._bot.send_message(chat_id=tg_id, text=text, reply_markup=markup)
