"""Сторож сообщений: кто написал боту после блокировки, снова получает вакансии."""

from datetime import UTC, datetime
from typing import Any

from aiogram.types import Chat, Message
from aiogram.types import User as TelegramUser

from app.domain.user.entities import User
from app.telegram.bot.middlewares.user_guard import UserGuardMiddleware


class FakeUsers:
    def __init__(self, user: User) -> None:
        self._user = user
        self.reactivated: list[int] = []

    async def get_user_by_tg_id(self, tg_id: int) -> User:
        return self._user

    async def reactivate(self, tg_id: int) -> None:
        self.reactivated.append(tg_id)


def _message(text: str) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=7, type="private"),
        from_user=TelegramUser(id=7, is_bot=False, first_name="Аня"),
        text=text,
    )


async def _run(user: User, text: str) -> tuple[FakeUsers, list[Any]]:
    handled: list[Any] = []

    async def handler(event: Any, data: dict[str, Any]) -> None:
        handled.append(event)

    users = FakeUsers(user)
    await UserGuardMiddleware()(handler, _message(text), {"user_service": users})
    return users, handled


async def test_message_from_blocked_user_brings_him_back() -> None:
    user = User.create(tg_id=7)
    user.deactivate()

    users, handled = await _run(user, "Мой профиль")

    assert users.reactivated == [7]
    assert len(handled) == 1


async def test_active_user_is_left_alone() -> None:
    users, handled = await _run(User.create(tg_id=7), "Мой профиль")

    assert users.reactivated == []
    assert len(handled) == 1
