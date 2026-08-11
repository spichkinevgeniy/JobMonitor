from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, MenuButtonCommands

from app.core.config import config

BASE_COMMANDS = [
    BotCommand(command="start", description="Открыть главное меню"),
    BotCommand(command="profile", description="Открыть профиль поиска"),
    BotCommand(command="settings", description="Настроить профиль и фильтры"),
    BotCommand(command="stats", description="Аналитика по вашему профилю"),
    BotCommand(command="help", description="Как это работает?"),
    BotCommand(command="privacy", description="Данные и приватность"),
    BotCommand(command="delete_me", description="Удалить мои данные"),
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


async def setup_menu_button(bot: Bot) -> None:
    """Кнопка слева от поля ввода — список команд.

    Задаём явно: настройка живёт на стороне Telegram и переживает перезапуск,
    так что убрать её из кода недостаточно, чтобы вернуть меню.
    """
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
