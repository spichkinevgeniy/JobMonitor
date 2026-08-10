from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonCommands


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть главное меню"),
            BotCommand(command="profile", description="Открыть профиль поиска"),
            BotCommand(command="settings", description="Настроить профиль и фильтры"),
            BotCommand(command="stats", description="Аналитика по вашему профилю"),
            BotCommand(command="help", description="Как это работает?"),
            BotCommand(command="privacy", description="Данные и приватность"),
            BotCommand(command="delete_me", description="Удалить мои данные"),
        ]
    )


async def setup_menu_button(bot: Bot) -> None:
    """Кнопка слева от поля ввода — список команд.

    Задаём явно: настройка живёт на стороне Telegram и переживает перезапуск,
    так что убрать её из кода недостаточно, чтобы вернуть меню.
    """
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
