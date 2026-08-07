"""Вход в аналитику через кнопку меню бота.

В reply-клавиатуре мини-апп не получает initData и авторизоваться не может,
поэтому вход сделан кнопкой меню — ей Telegram подписанные данные передаёт.
"""

from typing import Any

import pytest
from aiogram.types import MenuButtonCommands, MenuButtonWebApp

from app.telegram.bot import commands
from app.telegram.bot.commands import setup_menu_button
from app.telegram.bot.keyboards import (
    HELP_BUTTON_TEXT,
    PROFILE_BUTTON_TEXT,
    PROFILE_STATS_BUTTON_TEXT,
    get_main_menu_kb,
)


class FakeBot:
    def __init__(self) -> None:
        self.menu_button: Any = None

    async def set_chat_menu_button(self, menu_button: Any) -> None:
        self.menu_button = menu_button


async def test_menu_button_opens_the_mini_app() -> None:
    bot = FakeBot()

    await setup_menu_button(bot)  # type: ignore[arg-type]

    assert isinstance(bot.menu_button, MenuButtonWebApp)
    assert bot.menu_button.text == PROFILE_STATS_BUTTON_TEXT
    assert bot.menu_button.web_app.url.endswith("/miniapp/stats")


async def test_falls_back_to_commands_without_mini_app_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(commands, "build_stats_url", lambda: "")
    bot = FakeBot()

    await setup_menu_button(bot)  # type: ignore[arg-type]

    assert isinstance(bot.menu_button, MenuButtonCommands)


def test_main_menu_has_no_web_app_buttons() -> None:
    """Раньше тут стояла кнопка мини-аппа — она открывалась без initData."""
    rows = get_main_menu_kb().keyboard

    assert [[button.text for button in row] for row in rows] == [
        [PROFILE_BUTTON_TEXT, HELP_BUTTON_TEXT]
    ]
    assert all(button.web_app is None for row in rows for button in row)
