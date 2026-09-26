from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.application.ports.llm_port import IVacancyLLMExtractor
from app.application.ports.observability_port import IObservabilityService
from app.application.services.user_service import UserService
from app.bootstrap.models import RuntimeComponents
from app.core.config import config
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.infrastructure.extractors.jev_shadow import JevShadowVacancyExtractor
from app.infrastructure.extractors.vacancy_extractor import GoogleVacancyLLMExtractor
from app.infrastructure.jev import JevClient
from app.infrastructure.observability import (
    build_counter_store,
    build_observability_service,
    init_logfire,
    init_metrics_server,
    set_observability_service,
)
from app.infrastructure.sentry import init_sentry
from app.infrastructure.telegram.miniapp_server import build_miniapp_server
from app.infrastructure.telegram.telethon_client import TelethonClientProvider
from app.telegram.bot import get_router as get_bot_router
from app.telegram.bot.commands import setup_bot_commands, setup_menu_button
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
    scraper = TelegramScraper(
        client,
        bot,
        async_session_factory,
        build_vacancy_extractor(),
        observability,
    )
    return scraper, provider


def build_vacancy_extractor() -> IVacancyLLMExtractor:
    extractor: IVacancyLLMExtractor = GoogleVacancyLLMExtractor()
    if not config.JEV_SHADOW_ENABLED:
        return extractor
    return JevShadowVacancyExtractor(
        extractor,
        JevClient(config.OPENROUTER_API_KEY, config.JEV_MODEL),
        async_session_factory,
    )


async def build_runtime_components() -> RuntimeComponents:
    dp, bot = build_bot()
    await setup_bot_commands(bot)
    await setup_menu_button(bot)
    counter_store = build_counter_store()
    observability = build_observability_service(counter_store)
    set_observability_service(observability)
    user_service = UserService(UserUnitOfWork(async_session_factory), observability)
    scraper, provider = await build_scraper(bot, observability)
    miniapp_server = build_miniapp_server()
    return RuntimeComponents(
        dp=dp,
        bot=bot,
        scraper=scraper,
        provider=provider,
        miniapp_server=miniapp_server,
        user_service=user_service,
        counter_store=counter_store,
    )
