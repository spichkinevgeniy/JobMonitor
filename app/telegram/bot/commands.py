from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat

from app.core.config import config

BASE_COMMANDS = [
    BotCommand(command="start", description="Открыть главное меню"),
    BotCommand(command="profile", description="Открыть профиль поиска"),
    BotCommand(command="settings", description="Настроить профиль и фильтры"),
    BotCommand(command="help", description="Как это работает?"),
]

DEVELOPER_COMMANDS = [
    BotCommand(command="dev_reset_me", description="Сбросить dev-профиль"),
    BotCommand(command="dev_delete_me", description="Удалить dev-пользователя"),
]


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(BASE_COMMANDS)
    if config.APP_ENV != "development":
        return

    for tg_id in config.DEV_TELEGRAM_IDS:
        await bot.set_my_commands(
            [*BASE_COMMANDS, *DEVELOPER_COMMANDS],
            scope=BotCommandScopeChat(chat_id=tg_id),
        )
