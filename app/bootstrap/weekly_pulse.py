import asyncio
from datetime import UTC, datetime

from aiogram import Bot

from app.application.services.weekly_pulse_service import MSK, last_full_week
from app.core.config import config
from app.core.logger import get_app_logger
from app.infrastructure.db import UserUnitOfWork, VacancyUnitOfWork, async_session_factory
from app.telegram.bot.pulse_sender import WeeklyPulseSender
from app.telegram.bot.views import build_stats_url

logger = get_app_logger(__name__)

PULSE_CHECK_INTERVAL_SECONDS = 600
PULSE_WEEKDAY = 0  # понедельник
PULSE_START_HOUR = 10
# После вечера сводку за прошлую неделю уже не шлём: если прод лежал весь
# день, лучше пропустить неделю, чем прислать «итоги недели» ночью.
PULSE_END_HOUR = 22


def in_send_window(now: datetime) -> bool:
    local = now.astimezone(MSK)
    return local.weekday() == PULSE_WEEKDAY and PULSE_START_HOUR <= local.hour < PULSE_END_HOUR


async def run_weekly_pulse_loop(bot: Bot) -> None:
    """Раз в десять минут проверяет, пора ли слать сводку.

    Из цикла не выходим никогда: supervisor считает завершившуюся задачу
    аварией. Повторные запуски в то же окно безопасны — журнал сводок не
    даст отправить её человеку дважды.
    """
    sender = WeeklyPulseSender(
        bot=bot,
        user_uow_factory=lambda: UserUnitOfWork(async_session_factory),
        vacancy_uow_factory=lambda: VacancyUnitOfWork(async_session_factory),
        stats_url=build_stats_url(),
    )
    while True:
        now = datetime.now(UTC)
        if config.WEEKLY_PULSE_ENABLED and in_send_window(now):
            try:
                await sender.run(last_full_week(now))
            except Exception:
                logger.exception("Weekly pulse run failed")
        await asyncio.sleep(PULSE_CHECK_INTERVAL_SECONDS)
