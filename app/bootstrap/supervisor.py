import asyncio

from app.bootstrap.metrics_sync import run_metrics_sync_loop
from app.bootstrap.models import RuntimeComponents, RuntimeTasks
from app.bootstrap.shutdown import graceful_shutdown, install_shutdown_handlers
from app.infrastructure.telegram.miniapp_server import run_miniapp_server

# Потолок одновременно обрабатываемых апдейтов: по умолчанию aiogram не
# ограничивает их числом вовсе.
BOT_TASKS_CONCURRENCY_LIMIT = 50


def start_runtime_tasks(
    components: RuntimeComponents,
    stop_event: asyncio.Event,
) -> RuntimeTasks:
    return RuntimeTasks(
        scraper_task=asyncio.create_task(components.scraper.start(), name="scraper"),
        bot_task=asyncio.create_task(
            components.dp.start_polling(
                components.bot,
                handle_signals=False,
                close_bot_session=False,
                tasks_concurrency_limit=BOT_TASKS_CONCURRENCY_LIMIT,
            ),
            name="telegram-bot",
        ),
        miniapp_task=asyncio.create_task(
            run_miniapp_server(components.miniapp_server),
            name="miniapp-server",
        ),
        metrics_sync_task=asyncio.create_task(
            run_metrics_sync_loop(components.user_service),
            name="metrics-sync",
        ),
        stop_task=asyncio.create_task(stop_event.wait(), name="shutdown-signal"),
    )


async def wait_runtime(tasks: RuntimeTasks) -> None:
    all_tasks = {
        task
        for task in (
            tasks.scraper_task,
            tasks.bot_task,
            tasks.miniapp_task,
            tasks.metrics_sync_task,
            tasks.stop_task,
        )
        if task is not None
    }
    done, pending = await asyncio.wait(all_tasks, return_when=asyncio.FIRST_COMPLETED)

    if tasks.stop_task in done:
        return

    for task in pending:
        if task is tasks.stop_task:
            task.cancel()

    completed_tasks = [task for task in done if task is not tasks.stop_task]
    for task in completed_tasks:
        exc = task.exception()
        if exc is not None:
            raise exc

    finished_names = ", ".join(task.get_name() for task in completed_tasks)
    raise RuntimeError(f"Application task exited unexpectedly: {finished_names}")


async def run_supervised(components: RuntimeComponents) -> None:
    stop_event = asyncio.Event()
    installed_signals = install_shutdown_handlers(stop_event)
    tasks = RuntimeTasks()
    try:
        tasks = start_runtime_tasks(components, stop_event)
        await wait_runtime(tasks)
    finally:
        await graceful_shutdown(components, tasks, installed_signals)
