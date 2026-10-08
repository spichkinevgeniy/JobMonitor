"""Обработчики бота получают сервисы от bootstrap, а не открывают базу сами."""

import inspect
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import pytest
from aiogram import Router
from aiogram.types import Chat, Message, User

from app.bootstrap.bootstrap import build_bot_services
from app.telegram.bot.middlewares import ServicesMiddleware, UserGuardMiddleware
from app.telegram.bot.routers import (
    account,
    broadcast,
    help,
    onboarding,
    profile,
    pulse,
    resume,
    settings,
    vacancy_feedback,
)
from app.telegram.bot.views import build_start_required_text

ROUTERS = [account, broadcast, help, onboarding, profile, pulse, resume, settings, vacancy_feedback]
# Что aiogram передаёт обработчикам сам; остальное обязаны дать сервисы.
AIOGRAM_DATA = {"state", "command", "bot", "raw_state", "event_from_user", "event_chat"}


def _callbacks(router: Router) -> Iterator[Any]:
    for observer in router.observers.values():
        for handler in observer.handlers:
            yield handler.callback
    for sub_router in router.sub_routers:
        yield from _callbacks(sub_router)


def test_every_handler_gets_what_it_asks_for() -> None:
    """aiogram отдаёт сервис по имени параметра: опечатка тихо сломала бы кнопку."""
    services = build_bot_services().keys()
    unknown = [
        f"{callback.__module__}.{callback.__name__}({name})"
        for module in ROUTERS
        for callback in _callbacks(module.router)
        # Первый параметр — само событие: сообщение или нажатие кнопки.
        for name in list(inspect.signature(callback).parameters)[1:]
        if name not in services and name not in AIOGRAM_DATA
    ]

    assert unknown == []


async def test_services_are_fresh_for_every_update() -> None:
    """Единица работы держит сессию в себе — делить её между обновлениями нельзя."""
    seen: list[object] = []

    async def handler(event: object, data: dict[str, Any]) -> None:
        seen.append(data["user_service"])

    middleware = ServicesMiddleware(build_bot_services)
    await middleware(handler, object(), {})  # type: ignore[arg-type]
    await middleware(handler, object(), {})  # type: ignore[arg-type]

    assert seen[0] is not seen[1]


class _Users:
    def __init__(self, known: bool) -> None:
        self._known = known

    async def get_user_by_tg_id(self, tg_id: int) -> object | None:
        return object() if self._known else None


def _message(text: str) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=7, type="private"),
        from_user=User(id=7, is_bot=False, first_name="test"),
        text=text,
    )


class TestUserGuard:
    @pytest.fixture
    def answers(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        sent: list[str] = []

        async def fake_answer(self: Message, text: str, **kwargs: object) -> None:
            sent.append(text)

        monkeypatch.setattr(Message, "answer", fake_answer)
        return sent

    async def test_unknown_user_is_sent_to_start(self, answers: list[str]) -> None:
        passed: list[object] = []

        async def handler(event: object, data: dict[str, Any]) -> None:
            passed.append(event)

        await UserGuardMiddleware()(  # type: ignore[arg-type]
            handler, _message("/profile"), {"user_service": _Users(known=False)}
        )

        assert passed == []
        assert answers == [build_start_required_text()]

    async def test_known_user_goes_through(self, answers: list[str]) -> None:
        passed: list[object] = []

        async def handler(event: object, data: dict[str, Any]) -> None:
            passed.append(event)

        message = _message("/profile")
        await UserGuardMiddleware()(  # type: ignore[arg-type]
            handler, message, {"user_service": _Users(known=True)}
        )

        assert passed == [message]
        assert answers == []
