from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.application.ports.observability_port import IObservabilityService
from app.application.services.user_service import UserService
from app.bootstrap.models import RuntimeComponents
from app.core.config import config
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.infrastructure.extractors.vacancy_extractor import GoogleVacancyLLMExtractor
from app.infrastructure.observability import (
    build_observability_service,
    init_logfire,
    init_metrics_server,
)
from app.infrastructure.sentry import init_sentry
from app.infrastructure.telegram.miniapp_server import build_miniapp_server
from app.infrastructure.telegram.telethon_client import TelethonClientProvider
from app.telegram.bot import get_router as get_bot_router
from app.telegram.bot.commands import setup_bot_commands
from app.telegram.bot.middlewares import UserGuardMiddleware
from app.telegram.scrapper.handlers import TelegramScraper


def init_infrastructure() -> None:
    config.validate_runtime()
    init_sentry()
    init_logfire()
    init_metrics_server()


def build_bot() -> tuple[Dispatcher, Bot]:
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(UserGuardMiddleware(async_session_factory))
    dp.include_router(get_bot_router())
    return dp, bot


async def build_scraper(
    bot: Bot,
    observability: IObservabilityService,
) -> tuple[TelegramScraper, TelethonClientProvider]:
    provider = TelethonClientProvider()
    client = await provider.start()
    extractor = GoogleVacancyLLMExtractor()
    scraper = TelegramScraper(
        client,
        bot,
        async_session_factory,
        extractor,
        observability,
    )
    return scraper, provider


async def build_runtime_components() -> RuntimeComponents:
    dp, bot = build_bot()
    await setup_bot_commands(bot)
    observability = build_observability_service()
    await UserService(UserUnitOfWork(async_session_factory), observability).sync_user_metrics()
    scraper, provider = await build_scraper(bot, observability)
    miniapp_server = build_miniapp_server()
    return RuntimeComponents(
        dp=dp,
        bot=bot,
        scraper=scraper,
        provider=provider,
        miniapp_server=miniapp_server,
    )
