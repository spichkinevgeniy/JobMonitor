"""Вход в аналитику: кнопка в клавиатуре плюс inline-кнопка мини-аппа.

Reply-клавиатура не может открывать мини-апп напрямую — Telegram не передаёт
туда tgWebAppData, и initData приходит пустым.
"""

from typing import Any

from aiogram.types import MenuButtonCommands

from app.telegram.bot.commands import setup_menu_button
from app.telegram.bot.keyboards import (
    HELP_BUTTON_TEXT,
    PROFILE_BUTTON_TEXT,
    PROFILE_STATS_BUTTON_TEXT,
    get_main_menu_kb,
    get_stats_kb,
)


class FakeBot:
    def __init__(self) -> None:
        self.menu_button: Any = None

    async def set_chat_menu_button(self, menu_button: Any) -> None:
        self.menu_button = menu_button


async def test_menu_button_stays_the_commands_list() -> None:
    bot = FakeBot()

    await setup_menu_button(bot)  # type: ignore[arg-type]

    assert isinstance(bot.menu_button, MenuButtonCommands)


def test_stats_button_sits_next_to_profile() -> None:
    rows = get_main_menu_kb().keyboard

    assert [[button.text for button in row] for row in rows] == [
        [PROFILE_BUTTON_TEXT, PROFILE_STATS_BUTTON_TEXT],
        [HELP_BUTTON_TEXT],
    ]


def test_reply_keyboard_never_opens_the_mini_app() -> None:
    """Оттуда мини-апп открывается без initData — только обычный текст."""
    rows = get_main_menu_kb().keyboard

    assert all(button.web_app is None for row in rows for button in row)


def test_inline_button_opens_the_mini_app() -> None:
    button = get_stats_kb("https://example.test/miniapp/stats").inline_keyboard[0][0]

    assert button.text == PROFILE_STATS_BUTTON_TEXT
    assert button.web_app is not None
    assert button.web_app.url == "https://example.test/miniapp/stats"
