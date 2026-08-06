from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.application.ports.notification_port import IDocumentSender
from app.core.config import config


class TelegramDocumentSender(IDocumentSender):
    """Отправляет файл пользователю в чат с ботом.

    Мини-апп поднимается uvicorn'ом по строковому пути, поэтому боевой
    экземпляр Bot из bootstrap сюда не дотянуть. Заводим свой на время
    запроса: это тонкая обёртка над HTTP-сессией, а выгрузка — редкая
    операция. Контекстный менеджер закрывает сессию сам.
    """

    async def send_document(
        self,
        user_tg_id: int,
        filename: str,
        content: bytes,
        caption: str,
    ) -> None:
        async with Bot(token=config.BOT_TOKEN) as bot:
            await bot.send_document(
                chat_id=user_tg_id,
                document=BufferedInputFile(content, filename=filename),
                caption=caption,
            )
