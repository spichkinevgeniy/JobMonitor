from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject


class ServicesMiddleware(BaseMiddleware):
    """Кладёт в данные обработчика сервисы — свежие на каждое обновление.

    Собирает их bootstrap, поэтому Telegram-слою не нужно знать, как устроена
    база. Свежие — потому что единица работы держит сессию в себе и не
    переживает параллельные обработчики. aiogram отдаёт сервис аргументом
    с тем же именем, что и ключ.
    """

    def __init__(self, build: Callable[[], Mapping[str, Any]]) -> None:
        self._build = build

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data.update(self._build())
        return await handler(event, data)
