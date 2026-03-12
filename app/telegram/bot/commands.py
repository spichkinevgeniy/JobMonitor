from aiogram import Bot
from aiogram.types import BotCommand


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть главное меню"),
            BotCommand(command="profile", description="Открыть профиль поиска"),
            BotCommand(command="settings", description="Настроить профиль и фильтры"),
            BotCommand(command="help", description="Как это работает?"),
        ]
    )
