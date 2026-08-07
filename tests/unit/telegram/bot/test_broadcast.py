"""Рассылка заодно обновляет клавиатуру.

Telegram меняет reply-клавиатуру только вместе с сообщением, в котором
передана новая разметка. Рассылка — единственное, что доходит до всех сразу:
вакансии уходят через forward_message, а он клавиатуру не принимает.
"""

from types import SimpleNamespace
from typing import Any

import pytest
from aiogram.exceptions import TelegramForbiddenError

from app.telegram.bot.keyboards import PROFILE_STATS_BUTTON_TEXT, get_main_menu_kb
from app.telegram.bot.routers import broadcast as broadcast_router

ADMIN_ID = 1
TG_IDS = [101, 102, 103]


class FakeBot:
    def __init__(self, forbidden: set[int] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._forbidden = forbidden or set()

    async def send_message(self, chat_id: int, text: str, **kwargs: Any) -> None:
        if chat_id in self._forbidden:
            raise TelegramForbiddenError(method=None, message="blocked")  # type: ignore[arg-type]
        self.calls.append({"chat_id": chat_id, "text": text, **kwargs})


@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broadcast_router.config, "ADMIN_TG_IDS", str(ADMIN_ID))
    monkeypatch.setattr(broadcast_router, "SEND_DELAY_SECONDS", 0)

    class FakeUow:
        users = SimpleNamespace(list_active_tg_ids=lambda: _ids())

        async def __aenter__(self) -> "FakeUow":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

    async def _ids() -> list[int]:
        return TG_IDS

    monkeypatch.setattr(broadcast_router, "UserUnitOfWork", lambda factory: FakeUow())
    monkeypatch.setattr(broadcast_router, "_deactivate_user", _noop)


async def _noop(tg_id: int) -> None:
    return None


def _message(bot: FakeBot, tg_id: int = ADMIN_ID) -> Any:
    replies: list[str] = []

    async def answer(text: str, **kwargs: object) -> None:
        replies.append(text)

    return SimpleNamespace(
        from_user=SimpleNamespace(id=tg_id),
        bot=bot,
        answer=answer,
        replies=replies,
    )


async def _run(bot: FakeBot, text: str | None = "Привет", tg_id: int = ADMIN_ID) -> Any:
    message = _message(bot, tg_id)
    await broadcast_router.cmd_broadcast(message, SimpleNamespace(args=text))
    return message


async def test_every_message_carries_the_menu_keyboard() -> None:
    bot = FakeBot()

    await _run(bot)

    assert len(bot.calls) == len(TG_IDS)
    assert all(call["reply_markup"] == get_main_menu_kb() for call in bot.calls)


async def test_keyboard_contains_the_analytics_button() -> None:
    """Ради этого рассылка клавиатуру и обновляет."""
    bot = FakeBot()

    await _run(bot)

    texts = [button.text for row in bot.calls[0]["reply_markup"].keyboard for button in row]
    assert PROFILE_STATS_BUTTON_TEXT in texts


async def test_blocked_user_does_not_stop_the_rest() -> None:
    bot = FakeBot(forbidden={TG_IDS[0]})

    await _run(bot)

    assert [call["chat_id"] for call in bot.calls] == TG_IDS[1:]


async def test_non_admin_is_ignored() -> None:
    bot = FakeBot()

    await _run(bot, tg_id=999)

    assert bot.calls == []


async def test_empty_text_sends_nothing() -> None:
    bot = FakeBot()

    message = await _run(bot, text=None)

    assert bot.calls == []
    assert "Использование" in message.replies[0]
