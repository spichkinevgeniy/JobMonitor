"""Кнопки под вакансией собирает Telegram-слой, рассылка их только прикрепляет."""

from typing import Any
from uuid import UUID, uuid4

import pytest
from aiogram.types import InlineKeyboardMarkup

from app.application.ports.notification_port import DispatchTarget
from app.infrastructure.notifications import TelegramNotificationService


class FakeBot:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def copy_message(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


async def _skip_log(user_id: int, vacancy_id: UUID, target: DispatchTarget) -> None:
    return None


async def test_vacancy_goes_out_with_keyboard_from_telegram_layer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    built: list[tuple[str, str | None, str | None]] = []

    def keyboard(
        vacancy_id: str, *, source_channel: str | None, source_url: str | None
    ) -> InlineKeyboardMarkup:
        built.append((vacancy_id, source_channel, source_url))
        return markup

    bot = FakeBot()
    service = TelegramNotificationService(
        bot,  # type: ignore[arg-type]
        session_factory=None,  # type: ignore[arg-type]
        vacancy_keyboard=keyboard,
    )
    monkeypatch.setattr(service, "_log_dispatch", _skip_log)
    vacancy_id = uuid4()

    await service.dispatch_vacancy(
        vacancy_id,
        mirror_chat_id=-100,
        mirror_message_id=7,
        targets=[DispatchTarget(user_id=42)],
        source_channel="@jobs",
        source_url="https://t.me/jobs/1",
    )

    assert built == [(str(vacancy_id), "@jobs", "https://t.me/jobs/1")]
    assert bot.calls == [
        {"chat_id": 42, "from_chat_id": -100, "message_id": 7, "reply_markup": markup}
    ]
