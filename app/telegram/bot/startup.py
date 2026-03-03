from aiogram import Bot
from aiogram.types import BotCommand


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [BotCommand(command="start", description="Начать пользоваться ботом")]
    )
    await bot.set_my_description(
        "Помогаю мониторить вакансии, работать с резюме и управлять фильтрами."
    )
    await bot.set_my_short_description("Мониторинг вакансий")
