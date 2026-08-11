import asyncio

from app.application.services.user_service import UserService
from app.bootstrap.bootstrap import build_bot, build_scraper, init_infrastructure
from app.bootstrap.shutdown import install_shutdown_handlers, remove_shutdown_handlers
from app.core.logger import get_app_logger
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.infrastructure.observability import build_observability_service
from app.telegram.bot.commands import setup_bot_commands

logger = get_app_logger(__name__)


async def run_bot_component(*, with_scraper: bool = False) -> None:
    """Run the production bot wiring without the embedded Mini App server."""
    init_infrastructure()
    dispatcher, bot = build_bot()
    await setup_bot_commands(bot)

    observability = build_observability_service()
    user_service = UserService(UserUnitOfWork(async_session_factory), observability)
    await user_service.sync_user_metrics()

    provider = None
    scraper = None
    if with_scraper:
        scraper, provider = await build_scraper(bot, observability)

    stop_event = asyncio.Event()
    installed_signals = install_shutdown_handlers(stop_event)
    bot_task = asyncio.create_task(
        dispatcher.start_polling(
            bot,
            handle_signals=False,
            close_bot_session=False,
        ),
        name="telegram-bot",
    )
    scraper_task = (
        asyncio.create_task(scraper.start(), name="scraper") if scraper is not None else None
    )
    stop_task = asyncio.create_task(stop_event.wait(), name="shutdown-signal")
    tasks = {bot_task, stop_task}
    if scraper_task is not None:
        tasks.add(scraper_task)

    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        if stop_task not in done:
            finished = [task for task in done if task is not stop_task]
            for task in finished:
                exception = task.exception()
                if exception is not None:
                    raise exception
            names = ", ".join(task.get_name() for task in finished)
            raise RuntimeError(f"Bot runtime task exited unexpectedly: {names}")
    finally:
        remove_shutdown_handlers(installed_signals)
        try:
            await dispatcher.stop_polling()
        except RuntimeError:
            pass
        if provider is not None:
            await provider.stop()
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await bot.session.close()
        logger.info("Bot component stopped")


__all__ = ["run_bot_component"]
