from aiogram import Bot
from aiogram.types import (
    BotCommand,
    MenuButtonCommands,
    MenuButtonWebApp,
    WebAppInfo,
)

from app.core.logger import get_app_logger
from app.telegram.bot.keyboards import PROFILE_STATS_BUTTON_TEXT
from app.telegram.bot.views.settings import build_stats_url

logger = get_app_logger(__name__)


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть главное меню"),
            BotCommand(command="profile", description="Открыть профиль поиска"),
            BotCommand(command="settings", description="Настроить профиль и фильтры"),
            BotCommand(command="help", description="Как это работает?"),
        ]
    )


async def setup_menu_button(bot: Bot) -> None:
    """Кнопка слева от поля ввода. В reply-клавиатуре мини-апп не получает
    initData, а здесь получает."""
    stats_url = build_stats_url()
    if not stats_url:
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        logger.warning("Menu button reset to commands: mini app url is not configured")
        return

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=PROFILE_STATS_BUTTON_TEXT,
            web_app=WebAppInfo(url=stats_url),
        )
    )
