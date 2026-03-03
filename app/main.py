import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import config
from app.infrastructure.db import async_session_factory
from app.infrastructure.extractors.vacancy_extractor import GoogleVacancyLLMExtractor
from app.infrastructure.observability import (
    build_observability_service,
    init_logfire,
    init_metrics_server,
)
from app.infrastructure.sentry import init_sentry
from app.infrastructure.telegram.telethon_client import TelethonClientProvider
from app.telegram.bot import get_router as get_bot_router
from app.telegram.bot.middlewares import UserGuardMiddleware
from app.telegram.bot.startup import setup_bot_commands
from app.telegram.scrapper.handlers import TelegramScraper


async def build_scraper(bot: Bot) -> tuple[TelegramScraper, TelethonClientProvider]:
    provider = TelethonClientProvider()
    client = await provider.start()
    extractor = GoogleVacancyLLMExtractor()
    observability = build_observability_service()
    return TelegramScraper(client, bot, async_session_factory, extractor, observability), provider


def build_bot() -> tuple[Dispatcher, Bot]:
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(UserGuardMiddleware(async_session_factory))
    dp.include_router(get_bot_router())
    dp.startup.register(setup_bot_commands)
    return dp, bot


async def main() -> None:
    config.validate_runtime()
    init_sentry()
    init_logfire()
    init_metrics_server()
    dp, bot = build_bot()
    scraper, provider = await build_scraper(bot)

    try:
        scraper_task = asyncio.create_task(scraper.start())
        bot_task = asyncio.create_task(dp.start_polling(bot))
        await asyncio.gather(scraper_task, bot_task)
    finally:
        await provider.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
