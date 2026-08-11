from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher

from app.application.services.user_service import UserService
from app.infrastructure.telegram.miniapp_server import MiniAppServer

if TYPE_CHECKING:
    from app.infrastructure.telegram.telethon_client import TelethonClientProvider
    from app.telegram.scrapper.handlers import TelegramScraper


@dataclass(slots=True)
class RuntimeComponents:
    dp: Dispatcher
    bot: Bot
    scraper: TelegramScraper
    provider: TelethonClientProvider
    miniapp_server: MiniAppServer
    user_service: UserService


@dataclass(slots=True)
class RuntimeTasks:
    scraper_task: asyncio.Task[None] | None = None
    bot_task: asyncio.Task[None] | None = None
    miniapp_task: asyncio.Task[None] | None = None
    metrics_sync_task: asyncio.Task[None] | None = None
    stop_task: asyncio.Task[bool] | None = None

    def active(self) -> list[asyncio.Task[object]]:
        return [
            task
            for task in (
                self.scraper_task,
                self.bot_task,
                self.miniapp_task,
                self.metrics_sync_task,
                self.stop_task,
            )
            if task is not None and not task.done()
        ]
