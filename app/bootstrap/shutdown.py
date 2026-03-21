import asyncio
import signal
from contextlib import suppress

from aiogram import Bot, Dispatcher

from app.bootstrap.models import RuntimeComponents, RuntimeTasks
from app.core.logger import get_app_logger
from app.infrastructure.telegram.telethon_client import TelethonClientProvider

logger = get_app_logger(__name__)


def install_shutdown_handlers(stop_event: asyncio.Event) -> list[signal.Signals]:
    loop = asyncio.get_running_loop()
    installed_signals: list[signal.Signals] = []
    for shutdown_signal in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(shutdown_signal, stop_event.set)
            installed_signals.append(shutdown_signal)
    return installed_signals


def remove_shutdown_handlers(installed_signals: list[signal.Signals]) -> None:
    loop = asyncio.get_running_loop()
    for shutdown_signal in installed_signals:
        with suppress(NotImplementedError):
            loop.remove_signal_handler(shutdown_signal)


def request_component_shutdown(components: RuntimeComponents) -> None:
    components.miniapp_server.should_exit = True


async def stop_components(components: RuntimeComponents) -> None:
    await _stop_scraper(components.provider)
    await _stop_bot(components.dp)
    await _close_bot_session(components.bot)


async def await_task_shutdown(tasks: RuntimeTasks, timeout: float = 10) -> None:
    active_tasks = tasks.active()
    if not active_tasks:
        return

    try:
        await asyncio.wait_for(
            asyncio.gather(*active_tasks, return_exceptions=True),
            timeout=timeout,
        )
    except TimeoutError:
        for task in active_tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*active_tasks, return_exceptions=True)


async def graceful_shutdown(
    components: RuntimeComponents,
    tasks: RuntimeTasks,
    installed_signals: list[signal.Signals],
) -> None:
    remove_shutdown_handlers(installed_signals)
    request_component_shutdown(components)
    await stop_components(components)
    await await_task_shutdown(tasks)


async def _stop_scraper(provider: TelethonClientProvider) -> None:
    try:
        await provider.stop()
    except Exception:
        logger.exception("Failed to stop Telethon provider during shutdown")


async def _stop_bot(dp: Dispatcher) -> None:
    try:
        await dp.stop_polling()
    except RuntimeError:
        return
    except Exception:
        logger.exception("Failed to stop bot polling during shutdown")


async def _close_bot_session(bot: Bot) -> None:
    try:
        await bot.session.close()
    except Exception:
        logger.exception("Failed to close bot session during shutdown")
