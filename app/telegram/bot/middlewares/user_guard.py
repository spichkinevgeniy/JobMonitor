from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.telegram.bot.keyboards import START_BUTTON_TEXT, get_start_kb
from app.telegram.bot.views import build_start_required_text

logger = get_app_logger(__name__)


class UserGuardMiddleware(BaseMiddleware):
    """Пускает дальше только тех, кто уже нажал /start.

    Сервис пользователей кладёт в данные ServicesMiddleware — он стоит раньше.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.from_user is None:
            logger.warning("Message without from_user received, skipping")
            return None

        text = (event.text or "").strip()
        if text.startswith("/start") or text == START_BUTTON_TEXT:
            return await handler(event, data)

        users: UserService = data["user_service"]
        user = await users.get_user_by_tg_id(event.from_user.id)

        if user is None:
            await event.answer(
                build_start_required_text(),
                reply_markup=get_start_kb(),
            )
            return None

        return await handler(event, data)
